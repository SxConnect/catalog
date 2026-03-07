from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
import hashlib
import boto3
from botocore.exceptions import ClientError
from app.config import settings

class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_data: bytes, path: str) -> str:
        """Salva arquivo e retorna URL/path"""
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        """Retorna URL pública do arquivo"""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Remove arquivo"""
        pass

class FilesystemStorage(StorageBackend):
    def __init__(self, base_path: str = "/app/storage"):
        self.base_path = Path(base_path)
    
    def save(self, file_data: bytes, path: str) -> str:
        full_path = self.base_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(file_data)
        
        return str(full_path)
    
    def get_url(self, path: str) -> str:
        return f"/storage/{path}"
    
    def delete(self, path: str) -> bool:
        try:
            (self.base_path / path).unlink()
            return True
        except:
            return False

class S3Storage(StorageBackend):
    def __init__(self, bucket: str, endpoint: Optional[str] = None):
        self.bucket = bucket
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region
        )
    
    def save(self, file_data: bytes, path: str) -> str:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=path,
                Body=file_data,
                ContentType=self._get_content_type(path)
            )
            return path
        except ClientError as e:
            raise Exception(f"S3 upload error: {e}")
    
    def get_url(self, path: str) -> str:
        if settings.s3_public_url:
            return f"{settings.s3_public_url}/{self.bucket}/{path}"
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': path},
            ExpiresIn=3600
        )
    
    def delete(self, path: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=path)
            return True
        except:
            return False
    
    def _get_content_type(self, path: str) -> str:
        ext = Path(path).suffix.lower()
        types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.pdf': 'application/pdf'
        }
        return types.get(ext, 'application/octet-stream')

class StorageService:
    def __init__(self):
        storage_type = getattr(settings, 'storage_type', 'filesystem')
        
        if storage_type == 's3' or storage_type == 'minio':
            self.backend = S3Storage(
                bucket=settings.s3_bucket,
                endpoint=getattr(settings, 's3_endpoint', None)
            )
        else:
            self.backend = FilesystemStorage(settings.storage_path)
    
    def save_image(self, image_data: bytes, catalog_id: int, filename: str) -> str:
        """Salva imagem e retorna URL"""
        image_hash = hashlib.md5(image_data).hexdigest()
        path = f"products/images/{catalog_id}/{image_hash}.png"
        
        self.backend.save(image_data, path)
        return self.backend.get_url(path)
    
    def save_catalog(self, file_data: bytes, catalog_id: int, filename: str) -> str:
        """Salva catálogo PDF"""
        path = f"catalogs/{catalog_id}_{filename}"
        self.backend.save(file_data, path)
        return self.backend.get_url(path)
    
    def delete_image(self, path: str) -> bool:
        return self.backend.delete(path)

# Singleton
storage_service = StorageService()
