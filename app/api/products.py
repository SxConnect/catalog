from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.database import get_db
from app.models import Product
from app.middleware.security import rate_limit_products
from typing import List, Optional

router = APIRouter()

@router.get("/search")
@rate_limit_products()
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
