from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Catalog
from app.models.catalog import CatalogStatus
from app.tasks.pdf_processor import process_pdf_task
from app.middleware.security import (
    rate_limit_upload, 
    SecurityValidator, 
    FileValidationError,
    log_security_event
)
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
@rate_limit_upload()
async def upload_catalog(
    request: Request,
    file: UploadFile = File(..., description="PDF file (max 50MB)"), 
    db: Session = Depends(get_db)
):
    """
    Upload de catálogo PDF com validação de segurança.
    
    Rate limit: 10 requests por minuto por IP.
    Validações: extensão .pdf, tamanho máximo 50MB, nome de arquivo seguro.
    """
    logger.info(f"Recebendo upload: {file.filename}")
    
    try:
        # Validar arquivo antes de processar
        file_size = 0
        
        # Ler arquivo em chunks para calcular tamanho
        content = b""
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            file_size += len(chunk)
            content += chunk
        
        # Validar arquivo usando SecurityValidator
        SecurityValidator.validate_pdf_file(file.filename, file_size)
        
        # Log evento de segurança
        log_security_event(
            "file_upload_attempt",
            {
                "filename": file.filename,
                "file_size": file_size,
                "content_type": file.content_type
            },
            request
        )
        
    except FileValidationError as e:
        logger.error(f"Validação de arquivo falhou: {str(e)}")
        log_security_event(
            "file_validation_failed",
            {
                "filename": file.filename,
                "error": str(e),
                "file_size": file_size
            },
            request
        )
        raise HTTPException(status_code=400, detail=str(e))
    
    # Criar registro no banco
    logger.info(f"Criando registro no banco para: {file.filename}")
    catalog = Catalog(
        filename=file.filename,
        status=CatalogStatus.UPLOADED
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    logger.info(f"Catálogo criado com ID: {catalog.id}")
    
    # Salvar arquivo
    file_path = Path(f"/app/storage/catalogs/{catalog.id}_{file.filename}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Salvando arquivo em: {file_path}")
        with file_path.open("wb") as buffer:
            buffer.write(content)
        
        logger.info(f"Arquivo salvo com sucesso: {file_size} bytes")
        logger.info(f"Iniciando processamento assíncrono para catálogo {catalog.id}")
        
        # Log evento de sucesso
        log_security_event(
            "file_upload_success",
            {
                "catalog_id": catalog.id,
                "filename": file.filename,
                "file_size": file_size
            },
            request
        )
        
        process_pdf_task.delay(catalog.id, str(file_path))
        
        return {"catalog_id": catalog.id, "status": "processing"}
        
    except Exception as e:
        logger.error(f"Erro ao processar upload: {str(e)}")
        file_path.unlink(missing_ok=True)
        db.delete(catalog)
        db.commit()
        
        # Log evento de erro
        log_security_event(
            "file_upload_error",
            {
                "filename": file.filename,
                "error": str(e)
            },
            request
        )
        raise

@router.get("/list")
@rate_limit_products()
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
@rate_limit_products()
def get_catalog(catalog_id: int, db: Session = Depends(get_db)):
    catalog = db.query(Catalog).filter(Catalog.id == catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")
    return catalog
