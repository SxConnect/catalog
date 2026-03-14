from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.models import Product
from app.middleware.security import rate_limit_products
from typing import List, Optional

router = APIRouter()

@router.get("/")
def search_products(
    request: Request,
    q: str = Query(..., min_length=2),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """
    Busca produtos usando full-text search (GIN) e trigram (fuzzy)
    """
    # Full-text search usando GIN index
    results = db.query(Product).filter(
        Product.full_text.op('@@')(func.plainto_tsquery('portuguese', q))
    ).limit(limit).all()
    
    if not results:
        # Fallback para trigram fuzzy search
        results = db.query(Product).filter(
            or_(
                Product.name.op('%')(q),
                Product.brand.op('%')(q)
            )
        ).limit(limit).all()
    
    return {
        "query": q,
        "total": len(results),
        "products": results
    }

@router.get("/by-ean/{ean}")
@rate_limit_products()
def search_by_ean(request: Request, ean: str, db: Session = Depends(get_db)):
    """Busca exata por EAN usando index"""
    product = db.query(Product).filter(Product.ean == ean).first()
    if not product:
        return {"error": "Product not found"}
    return product

@router.get("/by-brand/{brand}")
@rate_limit_products()
def search_by_brand(
    request: Request,
    brand: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Busca por marca usando index"""
    products = db.query(Product).filter(
        Product.brand.ilike(f"%{brand}%")
    ).offset(skip).limit(limit).all()
    
    return {
        "brand": brand,
        "total": len(products),
        "products": products
    }
