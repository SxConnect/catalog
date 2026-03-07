from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product
from typing import List

router = APIRouter()

@router.get("/", response_model=List[dict])
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    return product

@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    return {"message": "CSV export endpoint"}

@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return {"products": [p.__dict__ for p in products]}
