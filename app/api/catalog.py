from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Catalog
from app.tasks.pdf_processor import process_pdf_task
import shutil
from pathlib import Path

router = APIRouter()

@router.post("/upload")
async def upload_catalog(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    catalog = Catalog(filename=file.filename)
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    
    file_path = Path(f"/app/storage/catalogs/{catalog.id}_{file.filename}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    process_pdf_task.delay(catalog.id, str(file_path))
    
    return {"catalog_id": catalog.id, "status": "processing"}

@router.get("/list")
def list_catalogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Lista todos os catálogos"""
    catalogs = db.query(Catalog).offset(skip).limit(limit).all()
    total = db.query(Catalog).count()
    
    return {
        "total": total,
        "catalogs": catalogs
    }

@router.get("/{catalog_id}")
def get_catalog(catalog_id: int, db: Session = Depends(get_db)):
    catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return catalog
