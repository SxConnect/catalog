"""
Worker para extração em massa da Cobasi
Roda em paralelo com o processamento de PDFs
Usa sistema de deduplicação unificado
"""
import asyncio
import asyncpg
import aiohttp
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin
import logging
from datetime import datetime
from celery import Celery
from app.config import DATABASE_URL
from app.logger import logger
from app.services.product_deduplication import ProductDeduplicator

# Configurar Celery para tarefas assíncronas
celery_app = Celery('cobasi_extractor')

class CobasiExtractor:
    def __init__(self):
        self.base_url = "https://www.cobasi.com.br"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        }
        self.deduplicator = ProductDeduplicator()
        self.stats = {
            'categories_processed': 0,
            'products_found': 0,
            'products_saved': 0,
            'products_updated': 0,
            'duplicates_found': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def get_db_connection(self):
        """Conexão com banco de dados"""
        return await asyncpg.connect(DATABASE_URL)
    
    async def create_cobasi_table(self):
        """Cria tabela unificada usando o deduplicador"""
        await self.deduplicator.create_unified_products_table()
        logger.info("✅ Tabela unificada criada/verificada")
    
    async def extract_category_urls(self):
        """Extrai todas as URLs de categorias da Cobasi"""
        logger.info("🔍 Extraindo URLs de categorias da Cobasi...")
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(f"{self.base_url}/institucional/categorias") as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Encontrar links de categorias
                    category_links = []
                    links = soup.find_all('a', href=re.compile(r'/c/'))
                    
                    for link in links:
                        href = link.get('href')
                        if href and href.startswith('/c/'):
                            full_url = self.base_url + href
                            if full_url not in category_links:
                                category_links.append(full_url)
                    
                    logger.info(f"📁 Encontradas {len(category_links)} categorias")
                    return category_links
                    
            except Exception as e:
                logger.error(f"❌ Erro ao extrair categorias: {e}")
                return []
    
    async def extract_products_from_category(self, category_url, session):
        """Extrai produtos de uma categoria específica"""
        try:
            async with session.get(category_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Encontrar links de produtos (padrão Cobasi: /p?idsku=)
                product_links = []
                links = soup.find_all('a', href=re.compile(r'/p\?idsku=\d+'))
                
                for link in links:
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = self.base_url + href
                        product_links.append(href)
                
                logger.info(f"🛍️ Categoria {category_url}: {len(product_links)} produtos")
                return product_links
                
        except Exception as e:
            logger.error(f"❌ Erro na categoria {category_url}: {e}")
            return []
    
    async def extract_product_details(self, product_url, session):
        """Extrai detalhes completos de um produto"""
        try:
            async with session.get(product_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extrair SKU da URL
                sku_match = re.search(r'idsku=(\d+)', product_url)
                sku = sku_match.group(1) if sku_match else None
                
                if not sku:
                    return None
                
                # Dados básicos
                product_data = {
                    'sku': sku,
                    'name': None,
                    'brand': None,
                    'price': None,
                    'source_url': product_url,
                    'images': [],
                    
                    # Ficha técnica
                    'porte': None,
                    'tipo_produto': None,
                    'peso_produto': None,
                    'sabor': None,
                    'idade_pet': None,
                    'linha_produto': None,
                    
                    # Nutricionais
                    'proteina_bruta': None,
                    'fosforo': None,
                    'calcio_min': None,
                    'energia_metabolizavel': None,
                    
                    # Composição
                    'ingredientes_principais': None,
                    'composicao_completa': None,
                    'descricao_completa': None,
                    'beneficios': [],
                    
                    # Metadados
                    'categoria_principal': 'Pet',
                    'is_enriched': True,
                    'enrichment_source': 'cobasi_direct',
                    'raw_data': {}
                }
                
                # Nome do produto
                name_elem = soup.select_one('h1')
                if name_elem:
                    product_data['name'] = name_elem.get_text(strip=True)
                
                # Preço
                price_elem = soup.select_one('[data-testid="price"], .price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    price_match = re.search(r'R\$\s*([\d.,]+)', price_text)
                    if price_match:
                        try:
                            price_str = price_match.group(1).replace('.', '').replace(',', '.')
                            product_data['price'] = float(price_str)
                        except:
                            pass
                
                # Marca (primeira palavra após "Ração")
                if product_data['name']:
                    words = product_data['name'].split()
                    for i, word in enumerate(words):
                        if word.lower() == 'ração' and i + 1 < len(words):
                            product_data['brand'] = words[i + 1]
                            break
                    if not product_data['brand'] and len(words) > 0:
                        product_data['brand'] = words[0]
                
                # Extrair dados do texto completo
                text_content = soup.get_text()
                
                # Ficha técnica
                ficha_patterns = {
                    'porte': r'Porte\s*([^\n]+)',
                    'tipo_produto': r'Tipo da Ração\s*([^\n]+)',
                    'peso_produto': r'Peso da Ração\s*([^\n]+)',
                    'sabor': r'Sabor da Ração\s*([^\n]+)',
                    'idade_pet': r'Idade\s*([^\n]+)',
                    'linha_produto': r'Linha\s*([^\n]+)'
                }
                
                for key, pattern in ficha_patterns.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        product_data[key] = match.group(1).strip()
                
                # Dados nutricionais
                nutri_patterns = {
                    'proteina_bruta': r'Proteína Bruta[^0-9]*(\d+[.,]?\d*)\s*g/kg',
                    'fosforo': r'Fósforo[^0-9]*(\d+[.,]?\d*)\s*mg/kg',
                    'calcio_min': r'Cálcio[^0-9]*(\d+[.,]?\d*)\s*mg/kg',
                    'energia_metabolizavel': r'Energia Metabolizável[^0-9]*(\d+[.,]?\d*)\s*kcal/kg'
                }
                
                for key, pattern in nutri_patterns.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        product_data[key] = match.group(1)
                
                # Composição
                comp_match = re.search(r'Composição Básica\s*([^A-Z]{100,800})', text_content, re.IGNORECASE | re.DOTALL)
                if comp_match:
                    product_data['composicao_completa'] = comp_match.group(1).strip()
                
                # Descrição
                desc_match = re.search(r'Detalhes do produto\s*([^A-Z]{50,300})', text_content, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    product_data['descricao_completa'] = desc_match.group(1).strip()
                
                # Salvar dados brutos
                product_data['raw_data'] = {
                    'html_text': text_content[:2000],  # Primeiros 2000 chars para análise
                    'extraction_date': datetime.now().isoformat()
                }
                
                return product_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair produto {product_url}: {e}")
            return None
    
    async def save_product(self, product_data):
        """Salva produto usando sistema de deduplicação"""
        try:
            result = await self.deduplicator.save_or_update_product(
                product_data, 
                source_type='cobasi',
                source_id=product_data.get('sku')
            )
            
            if result.get('id'):
                if result.get('created_at') == result.get('updated_at'):
                    self.stats['products_saved'] += 1
                    logger.info(f"💾 Novo produto Cobasi: {product_data['name']} (SKU: {product_data['sku']})")
                else:
                    self.stats['products_updated'] += 1
                    logger.info(f"🔄 Produto Cobasi atualizado: {product_data['name']} (SKU: {product_data['sku']})")
            else:
                self.stats['duplicates_found'] += 1
                logger.info(f"📋 Produto Cobasi já existe: {product_data['name']} (SKU: {product_data['sku']})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar produto Cobasi {product_data.get('sku')}: {e}")
            self.stats['errors'] += 1

@celery_app.task(bind=True)
def extract_cobasi_products(self):
    """Tarefa Celery para extração da Cobasi"""
    async def run_extraction():
        extractor = CobasiExtractor()
        
        # Criar tabela
        await extractor.create_cobasi_table()
        
        # Extrair categorias
        categories = await extractor.extract_category_urls()
        
        if not categories:
            logger.error("❌ Nenhuma categoria encontrada")
            return
        
        # Processar categorias
        async with aiohttp.ClientSession(headers=extractor.headers) as session:
            for category_url in categories[:5]:  # Começar com 5 categorias para teste
                logger.info(f"📁 Processando categoria: {category_url}")
                
                # Extrair produtos da categoria
                product_urls = await extractor.extract_products_from_category(category_url, session)
                
                # Processar produtos (máximo 10 por categoria para não sobrecarregar)
                for product_url in product_urls[:10]:
                    product_data = await extractor.extract_product_details(product_url, session)
                    
                    if product_data:
                        await extractor.save_product(product_data)
                    
                    # Delay entre produtos
                    await asyncio.sleep(1)
                
                extractor.stats['categories_processed'] += 1
                
                # Delay entre categorias
                await asyncio.sleep(2)
        
        # Log final
        elapsed = datetime.now() - extractor.stats['start_time']
        logger.info(f"🎉 Extração da Cobasi concluída!")
        logger.info(f"📊 Estatísticas:")
        logger.info(f"   - Categorias processadas: {extractor.stats['categories_processed']}")
        logger.info(f"   - Produtos novos: {extractor.stats['products_saved']}")
        logger.info(f"   - Produtos atualizados: {extractor.stats['products_updated']}")
        logger.info(f"   - Duplicatas encontradas: {extractor.stats['duplicates_found']}")
        logger.info(f"   - Erros: {extractor.stats['errors']}")
        logger.info(f"   - Tempo total: {elapsed}")
    
    # Executar extração
    asyncio.run(run_extraction())
    return "Extração da Cobasi concluída"