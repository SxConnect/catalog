import fitz
import pdfplumber
from pathlib import Path
from typing import List, Dict
import hashlib

class PDFService:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
    
    def get_total_pages(self) -> int:
        return len(self.doc)
    
    def extract_images_bytes(self, page_num: int) -> List[Dict]:
        """Extrai imagens como bytes (para S3/MinIO)"""
        page = self.doc[page_num]
        images = []
        
        for img_index, img in enumerate(page.get_images()):
            xref = img[0]
            base_image = self.doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            images.append({
                "bytes": image_bytes,
                "index": img_index,
                "page": page_num
            })
        
        return images
    
    def extract_images(self, page_num: int, output_dir: str) -> List[Dict]:
        """Extrai imagens para filesystem (legacy)"""
        page = self.doc[page_num]
        images = []
        
        for img_index, img in enumerate(page.get_images()):
            xref = img[0]
            base_image = self.doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            image_hash = hashlib.md5(image_bytes).hexdigest()
            image_path = Path(output_dir) / f"{image_hash}.png"
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            images.append({
                "path": str(image_path),
                "hash": image_hash,
                "page": page_num
            })
        
        return images
    
    def extract_text(self, page_num: int) -> str:
        with pdfplumber.open(self.pdf_path) as pdf:
            page = pdf.pages[page_num]
            return page.extract_text() or ""
    
    def close(self):
        self.doc.close()
