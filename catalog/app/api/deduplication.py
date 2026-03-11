from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.deduplication_service import DeduplicationService
from app.middleware.security import rate_limit_products, rate_limit_admin
from app.utils.cache import cache_deduplication_by_ean
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/check")
@rate_limit_products()
@cache_deduplication_by_ean(ttl=86400)  # Cache por 24 horas
def check_duplicate(
    request: Request,
    name: str = Query(..., min_length=2),
    brand: str = Query(..., min_length=2),
    ean: Optional[str] = None,
    threshold: float = Query(0.85, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Verifica se um produto é duplicata
    """
    dedup_service = DeduplicationService(db)
    duplicate = dedup_service.is_duplicate(name, brand, ean, threshold)
    
    if duplicate:
        return {
            "is_duplicate": True,
            "duplicate_product": {
                "id": duplicate.id,
                "name": duplicate.name,
                "brand": duplicate.brand,
                "ean": duplicate.ean
            }
        }
    
    return {"is_duplicate": False}

@router.get("/similar")
@rate_limit_products()
def find_similar(
    request: Request,
    name: str = Query(..., min_length=2),
    brand: str = Query(..., min_length=2),
    ean: Optional[str] = None,
    threshold: float = Query(0.6, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Busca produtos similares
    """
    dedup_service = DeduplicationService(db)
    similar = dedup_service.find_similar_products(name, brand, ean, threshold)
    
    return {
        "total": len(similar),
        "similar_products": [
            {
                "product": {
                    "id": s["product"].id,
                    "name": s["product"].name,
                    "brand": s["product"].brand,
                    "ean": s["product"].ean
                },
                "similarity": s["similarity"],
                "match_type": s["match_type"]
            }
            for s in similar
        ]
    }

@router.get("/find-all")
@rate_limit_products()
def find_all_duplicates(
    request: Request,
    threshold: float = Query(0.85, ge=0.0, le=1.0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Encontra todos os produtos duplicados no banco
    """
    dedup_service = DeduplicationService(db)
    duplicates = dedup_service.find_all_duplicates(threshold, limit)
    
    return {
        "total": len(duplicates),
        "duplicates": [
            {
                "product1": {
                    "id": d["product1"].id,
                    "name": d["product1"].name,
                    "brand": d["product1"].brand
                },
                "product2": {
                    "id": d["product2"].id,
                    "name": d["product2"].name,
                    "brand": d["product2"].brand
                },
                "similarity": d["similarity"]
            }
            for d in duplicates
        ]
    }

@router.post("/merge")
@rate_limit_admin()
def merge_duplicates(
    request: Request,
    keep_id: int,
    remove_id: int,
    db: Session = Depends(get_db)
):
    """
    Mescla dois produtos duplicados
    """
    dedup_service = DeduplicationService(db)
    success = dedup_service.merge_duplicates(keep_id, remove_id)
    
    if success:
        return {"message": "Products merged successfully"}
    
    return {"error": "Failed to merge products"}
