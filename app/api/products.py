from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.database import get_db
from app.models import Product
from app.middleware.security import rate_limit_products
from app.utils.cache import cache_products_list, cache_search_results, invalidate_products_cache
from app.services.nutrition_parser import nutrition_parser
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/search")
@rate_limit_products()
@cache_search_results(ttl=180)  # Cache por 3 minutos
def search_products(
    q: Optional[str] = Query(None, min_length=2),
    brand: Optional[str] = None,
    ean: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    sort_by: str = Query("name", pattern="^(name|brand|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """
    Busca produtos com filtros, paginação e ordenação
    """
    query = db.query(Product)
    
    # Filtros
    if q:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.description.ilike(f"%{q}%")
            )
        )
    
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    
    if ean:
        query = query.filter(Product.ean == ean)
    
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    
    # Total antes da paginação
    total = query.count()
    
    # Ordenação
    if sort_by == "name":
        query = query.order_by(asc(Product.name) if sort_order == "asc" else desc(Product.name))
    elif sort_by == "brand":
        query = query.order_by(asc(Product.brand) if sort_order == "asc" else desc(Product.brand))
    elif sort_by == "created_at":
        query = query.order_by(asc(Product.created_at) if sort_order == "asc" else desc(Product.created_at))
    
    # Paginação
    products = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": products
    }

@router.get("/", response_model=List[dict])
@rate_limit_products()
@cache_products_list(ttl=300)  # Cache por 5 minutos
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}")
@rate_limit_products()
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    return product

@router.get("/export/csv")
@rate_limit_products()
def export_csv(db: Session = Depends(get_db)):
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    products = db.query(Product).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["ID", "EAN", "Nome", "Marca", "Categoria", "Descrição", "Confiança", "Data Criação"])
    
    # Rows
    for p in products:
        writer.writerow([
            p.id,
            p.ean or "",
            p.name,
            p.brand,
            p.category or "",
            p.description or "",
            p.confidence_score or 0,
            p.created_at.isoformat() if p.created_at else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"}
    )

@router.get("/export/json")
@rate_limit_products()
def export_json(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return {"products": [p.__dict__ for p in products]}

@router.get("/{product_id}/ingredients")
@rate_limit_products()
def get_product_ingredients(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna ingredientes de um produto específico.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "brand": product.brand,
        "ingredients": product.ingredients or [],
        "ingredients_count": len(product.ingredients) if product.ingredients else 0
    }

@router.get("/{product_id}/nutrition")
@rate_limit_products()
def get_product_nutrition(product_id: int, db: Session = Depends(get_db)):
    """
    Retorna informações nutricionais de um produto específico.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "brand": product.brand,
        "nutritional_info": product.nutritional_info or {},
        "nutritional_values_count": len(product.nutritional_info) if product.nutritional_info else 0
    }

@router.get("/ingredients/search")
@rate_limit_products()
def search_by_ingredient(
    ingredient: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """
    Busca produtos que contêm um ingrediente específico.
    """
    # Usar operador JSON para buscar no array de ingredientes
    query = db.query(Product).filter(
        func.jsonb_exists(Product.ingredients, ingredient.lower())
    )
    
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    return {
        "ingredient": ingredient,
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": products
    }

@router.get("/nutrition/compare")
@rate_limit_products()
def compare_nutrition(
    product_ids: str = Query(..., description="IDs separados por vírgula, ex: 1,2,3"),
    db: Session = Depends(get_db)
):
    """
    Compara informações nutricionais entre produtos.
    """
    try:
        ids = [int(id.strip()) for id in product_ids.split(',')]
        if len(ids) > 5:
            return {"error": "Máximo 5 produtos para comparação"}
        
        products = db.query(Product).filter(Product.id.in_(ids)).all()
        
        if not products:
            return {"error": "Nenhum produto encontrado"}
        
        comparison = []
        for product in products:
            comparison.append({
                "id": product.id,
                "name": product.name,
                "brand": product.brand,
                "nutritional_info": product.nutritional_info or {},
                "ingredients_count": len(product.ingredients) if product.ingredients else 0
            })
        
        return {
            "products_compared": len(comparison),
            "comparison": comparison
        }
        
    except ValueError:
        return {"error": "IDs inválidos. Use números separados por vírgula"}

@router.post("/{product_id}/parse-nutrition")
@rate_limit_products()
def parse_product_nutrition(
    product_id: int,
    html_content: str,
    db: Session = Depends(get_db)
):
    """
    Faz parsing de informações nutricionais de HTML e atualiza o produto.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    try:
        # Fazer parsing das informações nutricionais
        nutritional_info = nutrition_parser.parse_nutritional_table(html_content)
        
        if nutritional_info:
            # Atualizar produto
            product.nutritional_info = nutritional_info
            db.commit()
            
            # Invalidar cache
            invalidate_products_cache()
            
            return {
                "success": True,
                "product_id": product_id,
                "nutritional_values_parsed": len(nutritional_info),
                "nutritional_info": nutritional_info
            }
        else:
            return {
                "success": False,
                "message": "Nenhuma informação nutricional encontrada no HTML"
            }
            
    except Exception as e:
        logger.error(f"Error parsing nutrition for product {product_id}: {e}")
        return {"error": f"Erro no parsing: {str(e)}"}

@router.post("/{product_id}/parse-ingredients")
@rate_limit_products()
def parse_product_ingredients(
    product_id: int,
    ingredients_text: str,
    db: Session = Depends(get_db)
):
    """
    Faz parsing de ingredientes de texto e atualiza o produto.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    try:
        # Fazer parsing dos ingredientes
        ingredients = nutrition_parser.parse_ingredients(ingredients_text)
        
        if ingredients:
            # Atualizar produto
            product.ingredients = ingredients
            db.commit()
            
            # Invalidar cache
            invalidate_products_cache()
            
            return {
                "success": True,
                "product_id": product_id,
                "ingredients_parsed": len(ingredients),
                "ingredients": ingredients
            }
        else:
            return {
                "success": False,
                "message": "Nenhum ingrediente encontrado no texto"
            }
            
    except Exception as e:
        logger.error(f"Error parsing ingredients for product {product_id}: {e}")
        return {"error": f"Erro no parsing: {str(e)}"}

@router.put("/{product_id}")
@rate_limit_products()
def update_product(
    product_id: int,
    product_data: dict,
    db: Session = Depends(get_db)
):
    """
    Atualiza um produto existente.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    try:
        # Campos que podem ser atualizados
        updatable_fields = [
            'name', 'brand', 'category', 'description', 'ean',
            'images', 'attributes', 'ingredients', 'nutritional_info'
        ]
        
        updated = False
        for field in updatable_fields:
            if field in product_data:
                setattr(product, field, product_data[field])
                updated = True
        
        if updated:
            # Atualizar timestamp
            product.updated_at = func.now()
            db.commit()
            
            # Invalidar cache
            invalidate_products_cache()
            
            return {
                "success": True,
                "product_id": product_id,
                "message": "Produto atualizado com sucesso"
            }
        else:
            return {
                "success": False,
                "message": "Nenhum campo válido para atualizar"
            }
            
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        db.rollback()
        return {"error": f"Erro ao atualizar produto: {str(e)}"}
