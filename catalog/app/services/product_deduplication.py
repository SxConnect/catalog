"""
Sistema de deduplicação e enriquecimento de produtos
Evita duplicatas e enriquece produtos de catálogos com dados web
"""
import asyncpg
import re
from typing import Optional, Dict, List
from app.logger import logger
from app.config import DATABASE_URL
from difflib import SequenceMatcher
import unicodedata

class ProductDeduplicator:
    def __init__(self):
        self.similarity_threshold = 0.85  # 85% de similaridade para considerar duplicata
        
    async def get_db_connection(self):
        """Conexão com banco de dados"""
        return await asyncpg.connect(DATABASE_URL)
    
    async def create_unified_products_table(self):
        """Cria tabela unificada para todos os produtos"""
        conn = await self.get_db_connection()
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS unified_products (
                    id SERIAL PRIMARY KEY,
                    
                    -- Identificadores únicos
                    sku VARCHAR(100),
                    ean VARCHAR(50),
                    name_normalized VARCHAR(500), -- Nome normalizado para busca
                    
                    -- Informações básicas
                    name VARCHAR(1000) NOT NULL,
                    brand VARCHAR(200),
                    price DECIMAL(10,2),
                    original_price DECIMAL(10,2),
                    discount_percentage INTEGER,
                    
                    -- URLs e imagens
                    source_url VARCHAR(1000),
                    images TEXT[], -- Array de URLs de imagens
                    
                    -- Ficha técnica (dados ricos da Cobasi/web)
                    porte VARCHAR(200),           -- Raças Pequenas, Médias, Grandes
                    tipo_produto VARCHAR(200),    -- Ração Seca, Ração Úmida, Petisco
                    peso_produto VARCHAR(200),    -- 1kg, 3kg, 15kg, etc.
                    sabor VARCHAR(500),          -- Frango, Carne, Salmão
                    idade_pet VARCHAR(100),      -- Filhote, Adulto, Senior
                    linha_produto VARCHAR(200),   -- Choice, Special, Premium
                    genero VARCHAR(50),          -- Unissex, Macho, Fêmea
                    
                    -- Dados nutricionais detalhados
                    proteina_bruta VARCHAR(50),
                    fosforo VARCHAR(50),
                    calcio_min VARCHAR(50),
                    calcio_max VARCHAR(50),
                    energia_metabolizavel VARCHAR(50),
                    umidade VARCHAR(50),
                    materia_fibrosa VARCHAR(50),
                    extrato_etereo VARCHAR(50),
                    
                    -- Vitaminas e minerais
                    vitamina_a VARCHAR(50),
                    vitamina_d3 VARCHAR(50),
                    vitamina_e VARCHAR(50),
                    zinco VARCHAR(50),
                    ferro VARCHAR(50),
                    
                    -- Composição e ingredientes
                    ingredientes_principais TEXT,
                    composicao_completa TEXT,
                    
                    -- Descrição e marketing
                    descricao_curta TEXT,
                    descricao_completa TEXT,
                    beneficios TEXT[],
                    indicacoes TEXT[],
                    
                    -- Classificação e categorização
                    categoria_principal VARCHAR(200),
                    subcategoria VARCHAR(200),
                    tags TEXT[],
                    
                    -- Origem dos dados
                    source_type VARCHAR(50) NOT NULL, -- 'cobasi', 'catalog', 'web_enriched'
                    source_id VARCHAR(100),           -- ID do catálogo ou site de origem
                    catalog_id INTEGER,               -- Referência ao catálogo se veio de PDF
                    
                    -- Enriquecimento
                    is_enriched BOOLEAN DEFAULT FALSE,
                    enriched_at TIMESTAMP WITH TIME ZONE,
                    enrichment_source VARCHAR(200),   -- URL ou fonte do enriquecimento
                    
                    -- Metadados
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    -- Dados brutos para análise
                    raw_data JSONB,
                    
                    -- Constraints
                    UNIQUE(sku, source_type) -- Permite mesmo SKU de fontes diferentes
                )
            """)
            
            # Índices para performance e deduplicação
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_name_normalized ON unified_products(name_normalized)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_sku ON unified_products(sku)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_ean ON unified_products(ean)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_brand_name ON unified_products(brand, name)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_source ON unified_products(source_type, source_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_unified_catalog ON unified_products(catalog_id)")
            
            logger.info("✅ Tabela unified_products criada/atualizada")
            
        finally:
            await conn.close()
    
    def normalize_product_name(self, name: str) -> str:
        """Normaliza nome do produto para comparação"""
        if not name:
            return ""
        
        # Converter para minúsculas
        normalized = name.lower()
        
        # Remover acentos
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Remover caracteres especiais e espaços extras
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remover palavras comuns que não ajudam na identificação
        stop_words = ['racao', 'para', 'caes', 'gatos', 'cao', 'gato', 'pet', 'pets', 'animal', 'animais']
        words = normalized.split()
        words = [w for w in words if w not in stop_words or len(words) <= 3]
        
        return ' '.join(words)
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calcula similaridade entre dois nomes de produtos"""
        norm1 = self.normalize_product_name(name1)
        norm2 = self.normalize_product_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    async def find_similar_products(self, product_name: str, brand: str = None, sku: str = None) -> List[Dict]:
        """Encontra produtos similares no banco"""
        conn = await self.get_db_connection()
        try:
            similar_products = []
            
            # 1. Busca exata por SKU (se fornecido)
            if sku:
                exact_sku = await conn.fetchrow(
                    "SELECT * FROM unified_products WHERE sku = $1",
                    sku
                )
                if exact_sku:
                    similar_products.append({
                        'product': dict(exact_sku),
                        'similarity': 1.0,
                        'match_type': 'exact_sku'
                    })
                    return similar_products
            
            # 2. Busca por nome normalizado
            normalized_name = self.normalize_product_name(product_name)
            
            # Buscar produtos com nomes similares
            query = """
                SELECT * FROM unified_products 
                WHERE name_normalized % $1 
                OR similarity(name_normalized, $1) > 0.3
            """
            params = [normalized_name]
            
            # Adicionar filtro por marca se fornecida
            if brand:
                query += " AND (brand ILIKE $2 OR brand IS NULL)"
                params.append(f"%{brand}%")
            
            query += " ORDER BY similarity(name_normalized, $1) DESC LIMIT 10"
            
            candidates = await conn.fetch(query, *params)
            
            # Calcular similaridade detalhada
            for candidate in candidates:
                similarity = self.calculate_similarity(product_name, candidate['name'])
                
                if similarity >= 0.5:  # Threshold mínimo para considerar
                    match_type = 'exact_name' if similarity >= 0.95 else 'similar_name'
                    
                    similar_products.append({
                        'product': dict(candidate),
                        'similarity': similarity,
                        'match_type': match_type
                    })
            
            # Ordenar por similaridade
            similar_products.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_products
            
        finally:
            await conn.close()
    
    async def check_for_duplicates(self, product_data: Dict) -> Optional[Dict]:
        """Verifica se produto já existe (duplicata)"""
        similar_products = await self.find_similar_products(
            product_data.get('name', ''),
            product_data.get('brand'),
            product_data.get('sku')
        )
        
        for similar in similar_products:
            if similar['similarity'] >= self.similarity_threshold:
                logger.info(f"🔍 Duplicata encontrada: {similar['match_type']} - Similaridade: {similar['similarity']:.2f}")
                return similar['product']
        
        return None
    
    async def save_or_update_product(self, product_data: Dict, source_type: str, source_id: str = None, catalog_id: int = None) -> Dict:
        """Salva produto ou atualiza se já existir"""
        conn = await self.get_db_connection()
        try:
            # Verificar duplicatas
            existing_product = await self.check_for_duplicates(product_data)
            
            if existing_product:
                # Produto já existe - atualizar com novos dados se necessário
                product_id = existing_product['id']
                
                # Atualizar apenas se os novos dados são mais completos
                update_fields = []
                update_values = []
                param_count = 0
                
                # Verificar quais campos podem ser atualizados
                updatable_fields = {
                    'price': product_data.get('price'),
                    'source_url': product_data.get('source_url'),
                    'images': product_data.get('images'),
                    'descricao_completa': product_data.get('descricao_completa')
                }
                
                for field, new_value in updatable_fields.items():
                    if new_value and (not existing_product.get(field) or len(str(new_value)) > len(str(existing_product.get(field, '')))):
                        param_count += 1
                        update_fields.append(f"{field} = ${param_count}")
                        update_values.append(new_value)
                
                if update_fields:
                    param_count += 1
                    update_query = f"""
                        UPDATE unified_products 
                        SET {', '.join(update_fields)}, updated_at = NOW()
                        WHERE id = ${param_count}
                        RETURNING *
                    """
                    update_values.append(product_id)
                    
                    updated_product = await conn.fetchrow(update_query, *update_values)
                    logger.info(f"🔄 Produto atualizado: {product_data.get('name')} (ID: {product_id})")
                    return dict(updated_product)
                else:
                    logger.info(f"📋 Produto já existe e está completo: {product_data.get('name')} (ID: {product_id})")
                    return existing_product
            
            else:
                # Produto novo - inserir
                normalized_name = self.normalize_product_name(product_data.get('name', ''))
                
                new_product = await conn.fetchrow("""
                    INSERT INTO unified_products (
                        sku, ean, name, name_normalized, brand, price, original_price,
                        source_url, images, porte, tipo_produto, peso_produto, sabor,
                        idade_pet, linha_produto, genero, proteina_bruta, fosforo,
                        calcio_min, energia_metabolizavel, ingredientes_principais,
                        composicao_completa, descricao_curta, descricao_completa,
                        beneficios, categoria_principal, subcategoria, source_type,
                        source_id, catalog_id, raw_data
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26,
                        $27, $28, $29, $30, $31
                    ) RETURNING *
                """,
                    product_data.get('sku'),
                    product_data.get('ean'),
                    product_data.get('name'),
                    normalized_name,
                    product_data.get('brand'),
                    product_data.get('price'),
                    product_data.get('original_price'),
                    product_data.get('source_url'),
                    product_data.get('images', []),
                    product_data.get('porte'),
                    product_data.get('tipo_produto'),
                    product_data.get('peso_produto'),
                    product_data.get('sabor'),
                    product_data.get('idade_pet'),
                    product_data.get('linha_produto'),
                    product_data.get('genero'),
                    product_data.get('proteina_bruta'),
                    product_data.get('fosforo'),
                    product_data.get('calcio_min'),
                    product_data.get('energia_metabolizavel'),
                    product_data.get('ingredientes_principais'),
                    product_data.get('composicao_completa'),
                    product_data.get('descricao_curta'),
                    product_data.get('descricao_completa'),
                    product_data.get('beneficios', []),
                    product_data.get('categoria_principal'),
                    product_data.get('subcategoria'),
                    source_type,
                    source_id,
                    catalog_id,
                    product_data.get('raw_data')
                )
                
                logger.info(f"💾 Novo produto salvo: {product_data.get('name')} (ID: {new_product['id']})")
                return dict(new_product)
                
        finally:
            await conn.close()
    
    async def enrich_catalog_product(self, catalog_product: Dict) -> Dict:
        """Enriquece produto de catálogo com dados web se não existir duplicata"""
        # Primeiro verificar se já existe produto similar com dados ricos
        similar_products = await self.find_similar_products(
            catalog_product.get('name', ''),
            catalog_product.get('brand')
        )
        
        # Se encontrou produto similar com dados ricos, usar esses dados
        for similar in similar_products:
            if similar['similarity'] >= self.similarity_threshold and similar['product'].get('is_enriched'):
                logger.info(f"🔍 Produto de catálogo já existe com dados ricos: {catalog_product.get('name')}")
                return similar['product']
        
        # Se não encontrou, fazer enriquecimento web
        enriched_data = await self.web_enrich_product(catalog_product)
        return enriched_data
    
    async def web_enrich_product(self, product_data: Dict) -> Dict:
        """Enriquece produto com dados da web (busca em sites)"""
        # TODO: Implementar busca web para enriquecimento
        # Por enquanto, retorna os dados originais marcados como não enriquecidos
        
        logger.info(f"🌐 Enriquecimento web para: {product_data.get('name')} (TODO: implementar)")
        
        # Marcar como tentativa de enriquecimento
        product_data['is_enriched'] = False
        product_data['enrichment_source'] = 'web_search_pending'
        
        return product_data