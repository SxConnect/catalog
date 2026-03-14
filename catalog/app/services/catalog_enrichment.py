"""
Serviço para enriquecimento de produtos extraídos de catálogos PDF
Integra com sistema de deduplicação e enriquecimento web
"""
import asyncio
from typing import Dict, List, Optional
from app.logger import logger
from app.services.product_deduplication import ProductDeduplicator
from app.services.web_enrichment import WebEnrichmentService
import re

class CatalogEnrichmentService:
    def __init__(self):
        self.deduplicator = ProductDeduplicator()
        self.web_enricher = WebEnrichmentService()
    
    async def process_catalog_product(self, catalog_product: Dict, catalog_id: int) -> Dict:
        """
        Processa produto de catálogo:
        1. Verifica se já existe no banco (deduplicação)
        2. Se não existe, enriquece com dados web
        3. Salva na tabela unificada
        """
        try:
            # Normalizar dados do catálogo para formato unificado
            normalized_product = self.normalize_catalog_product(catalog_product)
            
            # Verificar se produto já existe (duplicata)
            existing_product = await self.deduplicator.check_for_duplicates(normalized_product)
            
            if existing_product:
                logger.info(f"📋 Produto de catálogo já existe no banco: {normalized_product.get('name')}")
                
                # Associar produto existente ao catálogo
                await self.associate_product_to_catalog(existing_product['id'], catalog_id)
                
                return {
                    'status': 'existing',
                    'product_id': existing_product['id'],
                    'message': 'Produto já existe no banco de dados',
                    'existing_product': existing_product
                }
            
            else:
                logger.info(f"🆕 Novo produto de catálogo, iniciando enriquecimento: {normalized_product.get('name')}")
                
                # Enriquecer com dados web
                enriched_product = await self.web_enricher.enrich_product(normalized_product)
                
                # Salvar produto enriquecido
                saved_product = await self.deduplicator.save_or_update_product(
                    enriched_product,
                    source_type='catalog',
                    source_id=str(catalog_id),
                    catalog_id=catalog_id
                )
                
                return {
                    'status': 'new',
                    'product_id': saved_product['id'],
                    'message': 'Produto enriquecido e salvo com sucesso',
                    'enriched_product': saved_product
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar produto de catálogo: {e}")
            return {
                'status': 'error',
                'message': f'Erro no processamento: {str(e)}'
            }
    
    def normalize_catalog_product(self, catalog_product: Dict) -> Dict:
        """Normaliza produto de catálogo para formato unificado"""
        
        # Extrair informações básicas
        name = catalog_product.get('name', '').strip()
        brand = self.extract_brand_from_name(name)
        
        # Tentar extrair informações do nome
        product_info = self.extract_product_info_from_name(name)
        
        normalized = {
            'name': name,
            'brand': brand,
            'price': catalog_product.get('price'),
            'ean': catalog_product.get('ean'),
            'sku': catalog_product.get('sku'),
            
            # Informações extraídas do nome
            'porte': product_info.get('porte'),
            'tipo_produto': product_info.get('tipo_produto'),
            'peso_produto': product_info.get('peso'),
            'sabor': product_info.get('sabor'),
            'idade_pet': product_info.get('idade'),
            
            # Metadados do catálogo
            'categoria_principal': 'Pet',
            'descricao_curta': catalog_product.get('description', ''),
            'source_url': None,  # Produtos de catálogo não têm URL
            'images': [],
            
            # Status de enriquecimento
            'is_enriched': False,
            'enrichment_source': 'pending',
            
            # Dados originais do catálogo
            'raw_data': {
                'catalog_original': catalog_product,
                'extraction_method': 'pdf_catalog'
            }
        }
        
        return normalized
    
    def extract_brand_from_name(self, name: str) -> Optional[str]:
        """Extrai marca do nome do produto"""
        if not name:
            return None
        
        # Marcas conhecidas de pet food
        known_brands = [
            'Royal Canin', 'Hill\'s', 'Purina', 'Pedigree', 'Whiskas', 'Golden',
            'Premier', 'GranPlus', 'Biofresh', 'Farmina', 'Acana', 'Orijen',
            'Taste of the Wild', 'Blue Buffalo', 'Wellness', 'Canidae',
            'Eukanuba', 'Pro Plan', 'Friskies', 'Felix', 'Sheba'
        ]
        
        name_lower = name.lower()
        
        for brand in known_brands:
            if brand.lower() in name_lower:
                return brand
        
        # Se não encontrou marca conhecida, usar primeira palavra
        words = name.split()
        if len(words) > 0:
            # Pular palavras comuns
            skip_words = ['ração', 'racao', 'petisco', 'snack']
            for word in words:
                if word.lower() not in skip_words and len(word) > 2:
                    return word.title()
        
        return None
    
    def extract_product_info_from_name(self, name: str) -> Dict:
        """Extrai informações do produto a partir do nome"""
        if not name:
            return {}
        
        name_lower = name.lower()
        info = {}
        
        # Extrair porte
        if any(word in name_lower for word in ['pequeno', 'small', 'mini']):
            info['porte'] = 'Pequeno'
        elif any(word in name_lower for word in ['medio', 'médio', 'medium']):
            info['porte'] = 'Médio'
        elif any(word in name_lower for word in ['grande', 'large', 'maxi']):
            info['porte'] = 'Grande'
        
        # Extrair tipo de produto
        if any(word in name_lower for word in ['ração seca', 'racao seca', 'dry']):
            info['tipo_produto'] = 'Ração Seca'
        elif any(word in name_lower for word in ['ração úmida', 'racao umida', 'wet', 'sachê', 'sache', 'lata']):
            info['tipo_produto'] = 'Ração Úmida'
        elif any(word in name_lower for word in ['petisco', 'snack', 'biscoito', 'treat']):
            info['tipo_produto'] = 'Petisco'
        elif 'ração' in name_lower or 'racao' in name_lower:
            info['tipo_produto'] = 'Ração'
        
        # Extrair peso
        weight_match = re.search(r'(\d+[.,]?\d*)\s*(kg|g|quilos?|gramas?)', name_lower)
        if weight_match:
            weight_value = weight_match.group(1).replace(',', '.')
            weight_unit = weight_match.group(2)
            if 'g' in weight_unit and 'kg' not in weight_unit:
                info['peso'] = f"{weight_value}g"
            else:
                info['peso'] = f"{weight_value}kg"
        
        # Extrair sabor
        sabores = ['frango', 'carne', 'peixe', 'salmão', 'cordeiro', 'peru', 'pato', 'vegetais']
        found_sabores = []
        for sabor in sabores:
            if sabor in name_lower:
                found_sabores.append(sabor.title())
        
        if found_sabores:
            info['sabor'] = ', '.join(found_sabores)
        
        # Extrair idade
        if any(word in name_lower for word in ['filhote', 'puppy', 'kitten', 'junior']):
            info['idade'] = 'Filhote'
        elif any(word in name_lower for word in ['adulto', 'adult']):
            info['idade'] = 'Adulto'
        elif any(word in name_lower for word in ['senior', 'idoso', 'mature']):
            info['idade'] = 'Senior'
        
        return info
    
    async def associate_product_to_catalog(self, product_id: int, catalog_id: int):
        """Associa produto existente a um catálogo"""
        conn = await self.deduplicator.get_db_connection()
        try:
            # Criar tabela de associação se não existir
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS catalog_product_associations (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER REFERENCES unified_products(id),
                    catalog_id INTEGER,
                    associated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(product_id, catalog_id)
                )
            """)
            
            # Inserir associação
            await conn.execute("""
                INSERT INTO catalog_product_associations (product_id, catalog_id)
                VALUES ($1, $2)
                ON CONFLICT (product_id, catalog_id) DO NOTHING
            """, product_id, catalog_id)
            
            logger.info(f"🔗 Produto {product_id} associado ao catálogo {catalog_id}")
            
        finally:
            await conn.close()
    
    async def process_catalog_batch(self, products: List[Dict], catalog_id: int) -> Dict:
        """Processa lote de produtos de catálogo"""
        results = {
            'total_products': len(products),
            'new_products': 0,
            'existing_products': 0,
            'errors': 0,
            'processed_products': []
        }
        
        logger.info(f"📦 Processando lote de {len(products)} produtos do catálogo {catalog_id}")
        
        for i, product in enumerate(products, 1):
            logger.info(f"🔄 Processando produto {i}/{len(products)}: {product.get('name', 'Sem nome')}")
            
            result = await self.process_catalog_product(product, catalog_id)
            results['processed_products'].append(result)
            
            if result['status'] == 'new':
                results['new_products'] += 1
            elif result['status'] == 'existing':
                results['existing_products'] += 1
            elif result['status'] == 'error':
                results['errors'] += 1
            
            # Pequena pausa para não sobrecarregar
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Lote processado: {results['new_products']} novos, {results['existing_products']} existentes, {results['errors']} erros")
        
        return results