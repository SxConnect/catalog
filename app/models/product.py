from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import func
from app.database import Base

class Product(Base):
    __tablename__ = "products_catalog"
    
    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String(50), unique=True, index=True, nullable=True)
    name = Column(String(500), index=True)
    brand = Column(String(200), index=True)
    category = Column(String(200), index=True)
    description = Column(Text)
    images = Column(JSON)
    attributes = Column(JSON)
    ingredients = Column(JSON)  # Lista de ingredientes normalizados
    nutritional_info = Column(JSON)  # Informações nutricionais (proteína, gordura, etc.)
    source_catalog = Column(String(200))
    confidence_score = Column(Float)
    full_text = Column(TSVECTOR)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_product_search', 'name', 'brand', 'category'),
        Index('idx_product_ean_brand', 'ean', 'brand'),
        Index('idx_product_full_text', 'full_text', postgresql_using='gin'),
        Index('idx_product_name_trgm', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
        Index('idx_product_brand_trgm', 'brand', postgresql_using='gin', postgresql_ops={'brand': 'gin_trgm_ops'}),
    )
