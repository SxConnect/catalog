from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models import Product
from typing import List, Dict, Optional

class DeduplicationService:
    """
    Detecta produtos duplicados usando pg_trgm similarity
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_similar_products(
        self, 
        name: str, 
        brand: str, 
        ean: Optional[str] = None,
        similarity_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Busca produtos similares usando trigram similarity
        
        Args:
            name: Nome do produto
            brand: Marca
            ean: EAN (se disponível, busca exata)
            similarity_threshold: Limiar de similaridade (0.0 a 1.0)
        
        Returns:
            Lista de produtos similares com score
        """
        
        # Se tem EAN, busca exata primeiro
        if ean:
            exact_match = self.db.query(Product).filter(
                Product.ean == ean
            ).first()
            
            if exact_match:
                return [{
                    "product": exact_match,
                    "similarity": 1.0,
                    "match_type": "ean_exact"
                }]
        
        # Busca por similaridade de nome + marca
        query = text("""
            SELECT 
                id,
                name,
                brand,
                ean,
                category,
                (
                    similarity(name, :name) * 0.7 + 
                    similarity(brand, :brand) * 0.3
                ) as similarity_score
            FROM products_catalog
            WHERE 
                brand ILIKE :brand_pattern
                AND (
                    similarity(name, :name) > :threshold
                    OR name % :name
                )
            ORDER BY similarity_score DESC
            LIMIT 10
        """)
        
        results = self.db.execute(query, {
            "name": name,
            "brand": brand,
            "brand_pattern": f"%{brand}%",
            "threshold": similarity_threshold
        }).fetchall()
        
        similar_products = []
        for row in results:
            product = self.db.query(Product).filter(Product.id == row.id).first()
            similar_products.append({
                "product": product,
                "similarity": float(row.similarity_score),
                "match_type": "trigram_similarity"
            })
        
        return similar_products
    
    def is_duplicate(
        self,
        name: str,
        brand: str,
        ean: Optional[str] = None,
        strict_threshold: float = 0.85
    ) -> Optional[Product]:
        """
        Verifica se produto é duplicata
        
        Prioridade:
        1. EAN exato (se disponível)
        2. Similaridade nome + marca
        
        Returns:
            Produto duplicado se encontrado, None caso contrário
        """
        
        # PRIORIDADE 1: Busca por EAN (índice único)
        if ean:
            exact_match = self.db.query(Product).filter(
                Product.ean == ean
            ).first()
            
            if exact_match:
                return exact_match
        
        # PRIORIDADE 2: Busca por similaridade
        similar = self.find_similar_products(name, brand, None, strict_threshold)
        
        if similar and similar[0]["similarity"] >= strict_threshold:
            return similar[0]["product"]
        
        return None
    
    def find_all_duplicates(
        self,
        similarity_threshold: float = 0.85,
        limit: int = 100
    ) -> List[Dict]:
        """
        Encontra todos os produtos duplicados no banco
        
        Returns:
            Lista de grupos de duplicatas
        """
        query = text("""
            WITH product_pairs AS (
                SELECT 
                    p1.id as id1,
                    p2.id as id2,
                    p1.name as name1,
                    p2.name as name2,
                    p1.brand as brand1,
                    p2.brand as brand2,
                    (
                        similarity(p1.name, p2.name) * 0.7 + 
                        similarity(p1.brand, p2.brand) * 0.3
                    ) as similarity_score
                FROM products_catalog p1
                JOIN products_catalog p2 ON p1.id < p2.id
                WHERE 
                    p1.brand = p2.brand
                    AND similarity(p1.name, p2.name) > :threshold
            )
            SELECT * FROM product_pairs
            WHERE similarity_score >= :threshold
            ORDER BY similarity_score DESC
            LIMIT :limit
        """)
        
        results = self.db.execute(query, {
            "threshold": similarity_threshold,
            "limit": limit
        }).fetchall()
        
        duplicates = []
        for row in results:
            p1 = self.db.query(Product).filter(Product.id == row.id1).first()
            p2 = self.db.query(Product).filter(Product.id == row.id2).first()
            
            duplicates.append({
                "product1": p1,
                "product2": p2,
                "similarity": float(row.similarity_score)
            })
        
        return duplicates
    
    def merge_duplicates(
        self,
        keep_id: int,
        remove_id: int
    ) -> bool:
        """
        Mescla produtos duplicados
        
        Args:
            keep_id: ID do produto a manter
            remove_id: ID do produto a remover
        """
        keep = self.db.query(Product).filter(Product.id == keep_id).first()
        remove = self.db.query(Product).filter(Product.id == remove_id).first()
        
        if not keep or not remove:
            return False
        
        # Mesclar dados (prioriza produto com mais informações)
        if not keep.ean and remove.ean:
            keep.ean = remove.ean
        
        if not keep.description and remove.description:
            keep.description = remove.description
        
        # Mesclar imagens
        if remove.images:
            keep.images = list(set((keep.images or []) + remove.images))
        
        # Mesclar atributos
        if remove.attributes:
            keep.attributes = {**(keep.attributes or {}), **remove.attributes}
        
        # Aumentar confidence se ambos concordam
        if keep.name == remove.name and keep.brand == remove.brand:
            keep.confidence_score = min(1.0, (keep.confidence_score or 0.8) + 0.1)
        
        # Remover duplicata
        self.db.delete(remove)
        self.db.commit()
        
        return True
