from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from app.database import get_db
from app.models import Product, Catalog
from app.services.sitemap_service import SitemapService
from app.logger import logger
import asyncio

router = APIRouter()

class SitemapImportRequest(BaseModel):
    sitemap_url: HttpUrl
    catalog_id: int
    url_filter: Optional[str] = None  # Regex para filtrar URLs (ex: '/produto/')
    max_products: Optional[int] = None  # Limite de produtos
    auto_save: bool = True  # Salvar automaticamente no banco

class SitemapImportResponse(BaseModel):
    status: str
    message: str
    total_urls: int
    products_extracted: int
    products_saved: int
    errors: List[str] = []

@router.post("/import", response_model=SitemapImportResponse)
async def import_from_sitemap(
    request: SitemapImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Importa produtos a partir de um sitemap.xml
    
    Exemplo de uso:
    ```json
    {
        "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
        "catalog_id": 1,
        "url_filter": "/produto/",
        "max_products": 50,
        "auto_save": true
    }
    ```
    """
    # Verificar se catálogo existe
    catalog = db.query(Catalog).filter(Catalog.id == request.catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    service = SitemapService()
    
    try:
        # Processar sitemap
        logger.info(f"Starting sitemap import from {request.sitemap_url}")
        products_data = await service.process_sitemap(
            str(request.sitemap_url),
            url_filter=request.url_filter,
            max_products=request.max_products
        )
        
        products_saved = 0
        errors = []
        
        if request.auto_save:
            # Salvar produtos no banco
            for product_data in products_data:
                try:
                    # Verificar se produto já existe (por EAN ou nome+marca)
                    existing = None
                    if product_data.get('ean'):
                        existing = db.query(Product).filter(
                            Product.ean == product_data['ean']
                        ).first()
                    
                    if not existing and product_data.get('name') and product_data.get('brand'):
                        existing = db.query(Product).filter(
                            Product.name == product_data['name'],
                            Product.brand == product_data['brand']
                        ).first()
                    
                    if existing:
                        # Atualizar produto existente
                        if product_data.get('description'):
                            existing.description = product_data['description']
                        if product_data.get('category'):
                            existing.category = product_data['category']
                        if product_data.get('price'):
                            existing.metadata = existing.metadata or {}
                            existing.metadata['price'] = product_data['price']
                        if product_data.get('images'):
                            existing.metadata = existing.metadata or {}
                            existing.metadata['images'] = product_data['images']
                        if product_data.get('source_url'):
                            existing.metadata = existing.metadata or {}
                            existing.metadata['source_url'] = product_data['source_url']
                        
                        logger.info(f"Updated existing product: {existing.name}")
                    else:
                        # Criar novo produto
                        new_product = Product(
                            catalog_id=request.catalog_id,
                            name=product_data['name'],
                            brand=product_data.get('brand', 'Unknown'),
                            ean=product_data.get('ean'),
                            description=product_data.get('description'),
                            category=product_data.get('category'),
                            confidence_score=0.8,  # Score médio para produtos extraídos da web
                            metadata={
                                'source': 'sitemap',
                                'source_url': product_data['source_url'],
                                'price': product_data.get('price'),
                                'images': product_data.get('images', []),
                                'specifications': product_data.get('specifications', {})
                            }
                        )
                        db.add(new_product)
                        logger.info(f"Created new product: {new_product.name}")
                    
                    products_saved += 1
                    
                except Exception as e:
                    error_msg = f"Error saving product {product_data.get('name', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            db.commit()
        
        await service.close()
        
        return SitemapImportResponse(
            status="success",
            message=f"Successfully imported {products_saved} products from sitemap",
            total_urls=len(products_data),
            products_extracted=len(products_data),
            products_saved=products_saved,
            errors=errors
        )
        
    except Exception as e:
        await service.close()
        logger.error(f"Sitemap import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/preview")
async def preview_sitemap(
    sitemap_url: HttpUrl,
    url_filter: Optional[str] = None,
    max_urls: int = 10
):
    """
    Preview das URLs que serão processadas do sitemap
    Útil para testar filtros antes de importar
    """
    service = SitemapService()
    
    try:
        urls = await service.fetch_sitemap(str(sitemap_url))
        
        # Aplicar filtro se fornecido
        if url_filter:
            import re
            pattern = re.compile(url_filter)
            urls = [u for u in urls if pattern.search(u['url'])]
        
        # Limitar quantidade
        urls = urls[:max_urls]
        
        await service.close()
        
        return {
            "total_urls": len(urls),
            "sample_urls": urls,
            "filter_applied": url_filter
        }
        
    except Exception as e:
        await service.close()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-scrape")
async def test_scrape_url(url: HttpUrl):
    """
    Testa a extração de dados de uma URL específica
    Útil para verificar se o scraping está funcionando
    """
    service = SitemapService()
    
    try:
        product_data = await service.scrape_product_page(str(url))
        await service.close()
        
        if not product_data:
            raise HTTPException(status_code=404, detail="Could not extract product data from URL")
        
        return {
            "status": "success",
            "product_data": product_data
        }
        
    except Exception as e:
        await service.close()
        raise HTTPException(status_code=500, detail=str(e))
