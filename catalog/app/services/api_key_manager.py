from sqlalchemy.orm import Session
from app.models import ApiKey
from app.database import SessionLocal
from datetime import datetime

class ApiKeyManager:
    def __init__(self):
        self.current_index = 0
    
    def get_next_key(self) -> str:
        db = SessionLocal()
        try:
            keys = db.query(ApiKey).filter(
                ApiKey.status == True,
                ApiKey.used_today < ApiKey.daily_limit
            ).all()
            
            if not keys:
                return None
            
            key = keys[self.current_index % len(keys)]
            self.current_index += 1
            
            key.used_today += 1
            key.last_used = datetime.now()
            db.commit()
            
            return key.key
        finally:
            db.close()
