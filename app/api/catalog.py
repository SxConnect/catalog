from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Catalog
from app.models.catalog import CatalogStatus
from app.tasks.pdf_processor import process_pdf_task
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_catalog(file: UploadFile = File(..., description="PDF file (max 100MB)"), db: Session = Depends(get_db)):
    logger.info(f"Recebendo upload: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        logger.error(f"Arquivo não é PDF: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Verificar tamanho do arquivo (100MB = 100 * 1024 * 1024 bytes)
    max_size = 100 * 1024 * 1024
    file_size = 0
    
    logger.info(f"Criando registro no banco para: {file.filename}")
    catalog = Catalog(
        filename=file.filename,
        status=CatalogStatus.UPLOADED
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    logger.info(f"Catálogo criado com ID: {catalog.id}")
    
    file_path = Path(f"/app/storage/catalogs/{catalog.id}_{file.filename}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Salvando arquivo em: {file_path}")
        with file_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # Ler em chunks de 1MB
                file_size += len(chunk)
                if file_size > max_size:
                    logger.error(f"Arquivo muito grande: {file_size} bytes")
                    file_path.unlink(missing_ok=True)
                    db.delete(catalog)
                    db.commit()
                    raise HTTPException(status_code=413, detail="File too large (max 100MB)")
                buffer.write(chunk)
        
        logger.info(f"Arquivo salvo com sucesso: {file_size} bytes")
        logger.info(f"Iniciando processamento assíncrono para catálogo {catalog.id}")
        process_pdf_task.delay(catalog.id, str(file_path))
        
        return {"catalog_id": catalog.id, "status": "processing"}
    except Exception as e:
        logger.error(f"Erro ao processar upload: {str(e)}")
        file_path.unlink(missing_ok=True)
        db.delete(catalog)
        db.commit()
        raise

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
