from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.database import Base

class CatalogStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Catalog(Base):
    __tablename__ = "catalogs"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500))
    status = Column(Enum(CatalogStatus), default=CatalogStatus.UPLOADED, nullable=False)
    total_pages = Column(Integer)
    processed_pages = Column(Integer, default=0)
    products_found = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
