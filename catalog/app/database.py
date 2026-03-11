from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Log da URL do banco para debug (sem mostrar senha)
db_url_safe = settings.database_url.replace(settings.database_url.split('@')[0].split(':')[-1], '***')
logger.info(f"Connecting to database: {db_url_safe}")

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
