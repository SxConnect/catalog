from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Catalog, Product
from app.middleware.security import rate_limit_products
from typing import List, Dict
from datetime import datetime

router = APIRouter()

@router.get("/catalog/{catalog_id}/status")
@rate_limit_products()
def get_catalog_status(catalog_id: int, db: Session = Depends(get_db)):
    """
    Retorna status detalhado do processamento do catálogo
    Use para polling e acompanhamento em tempo real
    """
    catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    # Contar produtos do catálogo
    products_count = db.query(Product).filter(
        Product.source_catalog == catalog.filename
    ).count()
    
    # Calcular progresso
    progress = 0
    if catalog.total_pages and catalog.total_pages > 0:
        progress = int((catalog.processed_pages or 0) / catalog.total_pages * 100)
    
    # Estimar tempo restante
    estimated_time_remaining = None
    if catalog.status == "processing" and catalog.total_pages and catalog.processed_pages:
        if catalog.processed_pages > 0:
            # Estimar baseado no tempo decorrido
            elapsed = (datetime.utcnow() - catalog.created_at).total_seconds()
            time_per_page = elapsed / catalog.processed_pages
            pages_remaining = catalog.total_pages - catalog.processed_pages
            estimated_time_remaining = int(time_per_page * pages_remaining)
    
    return {
        "catalog_id": catalog.id,
        "filename": catalog.filename,
        "status": catalog.status,
        "total_pages": catalog.total_pages,
        "processed_pages": catalog.processed_pages or 0,
        "progress_percentage": progress,
        "products_found": catalog.products_found or 0,
        "products_in_db": products_count,
        "created_at": catalog.created_at.isoformat() if catalog.created_at else None,
        "updated_at": catalog.updated_at.isoformat() if catalog.updated_at else None,
        "estimated_time_remaining_seconds": estimated_time_remaining,
        "is_processing": catalog.status == "processing",
        "is_completed": catalog.status == "completed",
        "is_failed": catalog.status == "failed"
    }

@router.get("/catalog/{catalog_id}/products")
@rate_limit_products()
def get_catalog_products(
    catalog_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Lista produtos extraídos de um catálogo específico
    """
    catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    products = db.query(Product).filter(
        Product.source_catalog == catalog.filename
    ).offset(skip).limit(limit).all()
    
    total = db.query(Product).filter(
        Product.source_catalog == catalog.filename
    ).count()
    
    return {
        "catalog_id": catalog_id,
        "total": total,
        "products": products
    }

@router.get("/recent")
@rate_limit_products()
def get_recent_catalogs(limit: int = 10, db: Session = Depends(get_db)):
    """
    Lista catálogos recentes com status
    """
    catalogs = db.query(Catalog).order_by(
        Catalog.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for catalog in catalogs:
        products_count = db.query(Product).filter(
            Product.source_catalog == catalog.filename
        ).count()
        
        progress = 0
        if catalog.total_pages and catalog.total_pages > 0:
            progress = int((catalog.processed_pages or 0) / catalog.total_pages * 100)
        
        result.append({
            "id": catalog.id,
            "filename": catalog.filename,
            "status": catalog.status,
            "progress_percentage": progress,
            "products_found": catalog.products_found or 0,
            "products_in_db": products_count,
            "created_at": catalog.created_at.isoformat() if catalog.created_at else None
        })
    
    return {"catalogs": result}

@router.get("/stats")
@rate_limit_products()
def get_processing_stats(db: Session = Depends(get_db)):
    """
    Estatísticas gerais de processamento
    """
    total_catalogs = db.query(Catalog).count()
    processing = db.query(Catalog).filter(Catalog.status == "processing").count()
    completed = db.query(Catalog).filter(Catalog.status == "completed").count()
    failed = db.query(Catalog).filter(Catalog.status == "failed").count()
    total_products = db.query(Product).count()
    
    return {
        "total_catalogs": total_catalogs,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total_products": total_products
    }
