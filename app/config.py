from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    groq_api_keys: str
    
    # Storage Configuration
    storage_type: str = "filesystem"  # filesystem, s3, minio
    storage_path: str = "/app/storage"
    
    # S3/MinIO Configuration
    s3_endpoint: Optional[str] = None  # For MinIO: http://minio:9000
    s3_bucket: str = "sixpet-catalog"
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_region: str = "us-east-1"
    s3_public_url: Optional[str] = None  # For public CDN URL
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"

settings = Settings()
