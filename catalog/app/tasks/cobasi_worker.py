"""
Worker para extração em massa da Cobasi
Roda em paralelo com o processamento de PDFs
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
        self.stats = {
            'categories_processed': 0,
            'products_found': 0,
            'products_saved': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    async def get_db_connection(self):
        """Conexão com banco de dados"""
        return await asyncpg.connect(DATABASE_URL)
    
    async def create_cobasi_table(self):
        """Cria tabela específica para produtos da Cobasi"""
        conn = await self.get_db_connection()
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS cobasi_products (
                    id SERIAL PRIMARY KEY,
                    sku VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(1000),
                    brand VARCHAR(200),
                    price DECIMAL(10,2),
                    url VARCHAR(1000),
                    images TEXT[],
                    
                    -- Ficha técnica
                    porte VARCHAR(200),
                    tipo_racao VARCHAR(200),
                    peso_racao VARCHAR(200),
                    sabor_racao VARCHAR(500),
                    idade VARCHAR(100),
                    linha VARCHAR(200),
                    
                    -- Nutricionais
                    proteina_bruta VARCHAR(50),
                    fosforo VARCHAR(50),
                    calcio VARCHAR(50),
                    energia_metabolizavel VARCHAR(50),
                    
                    -- Composição
                    ingredientes TEXT,
                    descricao TEXT,
                    beneficios TEXT[],
                    
                    -- Metadados
                    categoria VARCHAR(500),
                    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    -- Dados completos em JSON
                    raw_data JSONB
                )
            """)
            
            # Índices
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_cobasi_sku ON cobasi_products(sku)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_cobasi_brand ON cobasi_products(brand)")
            
            logger.info("✅ Tabela cobasi_products criada/verificada")
        finally:
            await conn.close()
    
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
                    'url': product_url,
                    'name': None,
                    'brand': None,
                    'price': None,
                    'images': [],
                    'ficha_tecnica': {},
                    'nutricionais': {},
                    'composicao': None,
                    'descricao': None,
                    'beneficios': []
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
                    'tipo_racao': r'Tipo da Ração\s*([^\n]+)',
                    'peso_racao': r'Peso da Ração\s*([^\n]+)',
                    'sabor_racao': r'Sabor da Ração\s*([^\n]+)',
                    'idade': r'Idade\s*([^\n]+)',
                    'linha': r'Linha\s*([^\n]+)'
                }
                
                for key, pattern in ficha_patterns.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        product_data['ficha_tecnica'][key] = match.group(1).strip()
                
                # Dados nutricionais
                nutri_patterns = {
                    'proteina_bruta': r'Proteína Bruta[^0-9]*(\d+[.,]?\d*)\s*g/kg',
                    'fosforo': r'Fósforo[^0-9]*(\d+[.,]?\d*)\s*mg/kg',
                    'calcio': r'Cálcio[^0-9]*(\d+[.,]?\d*)\s*mg/kg',
                    'energia_metabolizavel': r'Energia Metabolizável[^0-9]*(\d+[.,]?\d*)\s*kcal/kg'
                }
                
                for key, pattern in nutri_patterns.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        product_data['nutricionais'][key] = match.group(1)
                
                # Composição
                comp_match = re.search(r'Composição Básica\s*([^A-Z]{100,800})', text_content, re.IGNORECASE | re.DOTALL)
                if comp_match:
                    product_data['composicao'] = comp_match.group(1).strip()
                
                # Descrição
                desc_match = re.search(r'Detalhes do produto\s*([^A-Z]{50,300})', text_content, re.IGNORECASE | re.DOTALL)
                if desc_match:
                    product_data['descricao'] = desc_match.group(1).strip()
                
                return product_data
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair produto {product_url}: {e}")
            return None
    
    async def save_product(self, product_data):
        """Salva produto no banco de dados"""
        conn = await self.get_db_connection()
        try:
            await conn.execute("""
                INSERT INTO cobasi_products (
                    sku, name, brand, price, url, images,
                    porte, tipo_racao, peso_racao, sabor_racao, idade, linha,
                    proteina_bruta, fosforo, calcio, energia_metabolizavel,
                    ingredientes, descricao, raw_data
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16,
                    $17, $18, $19
                ) ON CONFLICT (sku) DO UPDATE SET
                    name = EXCLUDED.name,
                    brand = EXCLUDED.brand,
                    price = EXCLUDED.price,
                    updated_at = NOW()
            """,
                product_data['sku'],
                product_data['name'],
                product_data['brand'],
                product_data['price'],
                product_data['url'],
                product_data['images'],
                product_data['ficha_tecnica'].get('porte'),
                product_data['ficha_tecnica'].get('tipo_racao'),
                product_data['ficha_tecnica'].get('peso_racao'),
                product_data['ficha_tecnica'].get('sabor_racao'),
                product_data['ficha_tecnica'].get('idade'),
                product_data['ficha_tecnica'].get('linha'),
                product_data['nutricionais'].get('proteina_bruta'),
                product_data['nutricionais'].get('fosforo'),
                product_data['nutricionais'].get('calcio'),
                product_data['nutricionais'].get('energia_metabolizavel'),
                product_data['composicao'],
                product_data['descricao'],
                json.dumps(product_data)
            )
            
            self.stats['products_saved'] += 1
            logger.info(f"💾 Produto salvo: {product_data['name']} (SKU: {product_data['sku']})")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar produto {product_data['sku']}: {e}")
            self.stats['errors'] += 1
        finally:
            await conn.close()

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
        logger.info(f"🎉 Extração concluída!")
        logger.info(f"📊 Estatísticas:")
        logger.info(f"   - Categorias processadas: {extractor.stats['categories_processed']}")
        logger.info(f"   - Produtos salvos: {extractor.stats['products_saved']}")
        logger.info(f"   - Erros: {extractor.stats['errors']}")
        logger.info(f"   - Tempo total: {elapsed}")
    
    # Executar extração
    asyncio.run(run_extraction())
    return "Extração da Cobasi concluída"