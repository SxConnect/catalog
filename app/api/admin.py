from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Catalog, Product, ApiKey

router = APIRouter()

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_catalogs = db.query(func.count(Catalog.id)).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    processing = db.query(func.count(Catalog.id)).filter(
        Catalog.status == "processing"
    ).scalar()
    
    return {
        "total_catalogs": total_catalogs,
        "total_products": total_products,
        "processing": processing
    }

@router.get("/api-keys")
def list_api_keys(db: Session = Depends(get_db)):
    keys = db.query(ApiKey).all()
    return keys

@router.get("/queue/status")
def queue_status():
    return {"message": "Queue status endpoint"}
