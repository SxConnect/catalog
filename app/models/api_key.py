from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class ApiKey(Base):
    __tablename__ = "ai_api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(500), unique=True)
    provider = Column(String(50))
    daily_limit = Column(Integer)
    used_today = Column(Integer, default=0)
    status = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
