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

from pydantic import BaseModel

class ApiKeyCreate(BaseModel):
    key: str
    provider: str = "groq"
    daily_limit: int = 14400

@router.post("/api-keys")
def create_api_key(
    data: ApiKeyCreate,
    db: Session = Depends(get_db)
):
    """Cria uma nova API key"""
    # Verificar se já existe
    existing = db.query(ApiKey).filter(ApiKey.key == data.key).first()
    if existing:
        return {"error": "API key already exists", "id": existing.id}
    
    # Criar nova
    api_key = ApiKey(
        key=data.key,
        provider=data.provider,
        daily_limit=data.daily_limit,
        used_today=0,
        status=True
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return api_key

@router.delete("/api-keys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    """Remove uma API key"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        return {"error": "API key not found"}
    
    db.delete(api_key)
    db.commit()
    
    return {"message": "API key deleted successfully"}

@router.get("/queue/status")
def queue_status():
    return {"message": "Queue status endpoint"}

from app.models import Settings
from pydantic import BaseModel
from typing import Optional

class SettingsUpdate(BaseModel):
    groq_api_keys: str
    extractions_per_second: int = 10
    scraping_url: Optional[str] = None
    scraping_enabled: bool = False
    max_concurrent_catalogs: int = 4
    enable_deduplication: bool = True
    similarity_threshold: float = 0.85

@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    """Retorna todas as configurações do sistema"""
    settings_dict = {}
    
    # Valores padrão
    defaults = {
        "groq_api_keys": "",
        "extractions_per_second": 10,
        "scraping_url": "",
        "scraping_enabled": False,
        "max_concurrent_catalogs": 4,
        "enable_deduplication": True,
        "similarity_threshold": 0.85,
    }
    
    # Buscar do banco
    settings = db.query(Settings).all()
    for setting in settings:
        settings_dict[setting.key] = setting.get_typed_value()
    
    # Mesclar com defaults
    return {**defaults, **settings_dict}

@router.put("/settings")
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """Atualiza as configurações do sistema"""
    settings_data = {
        "groq_api_keys": ("string", data.groq_api_keys),
        "extractions_per_second": ("int", str(data.extractions_per_second)),
        "scraping_url": ("string", data.scraping_url or ""),
        "scraping_enabled": ("bool", str(data.scraping_enabled)),
        "max_concurrent_catalogs": ("int", str(data.max_concurrent_catalogs)),
        "enable_deduplication": ("bool", str(data.enable_deduplication)),
        "similarity_threshold": ("float", str(data.similarity_threshold)),
    }
    
    for key, (value_type, value) in settings_data.items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
            setting.value_type = value_type
        else:
            setting = Settings(
                key=key,
                value=value,
                value_type=value_type
            )
            db.add(setting)
    
    db.commit()
    return {"message": "Settings updated successfully"}
