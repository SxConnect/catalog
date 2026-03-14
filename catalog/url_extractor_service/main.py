"""
Microserviço independente para extração de URLs
Roda em porta separada para evitar conflitos de rotas do FastAPI principal
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import asyncpg
import os
import logging
from typing import Optional, List
import json

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="URL Extractor Service", 
    version="1.0.0",
    description="Microserviço independente para extração inteligente de produtos de URLs"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/catalog")

async def get_db_connection():
    """Conexão direta com PostgreSQL usando asyncpg"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "URL Extractor Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "GET /health - Health check",
            "GET /debug - Debug info", 
            "GET /products - List extracted products",
            "GET /smart-extract - Smart URL extraction",
            "POST /test-scrape - Test URL scraping"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy", "service": "url-extractor"}

@app.get("/debug")
async def debug_info():
    """Debug information"""
    return {
        "status": "debug",
        "service": "url-extractor",
        "message": "URL Extractor microservice is working",
        "database_url": DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else "configured",
        "endpoints_available": 5
    }

@app.get("/products")
async def list_products(limit: int = Query(10, description="Maximum number of products")):
    """List extracted products"""
    conn = await get_db_connection()
    try:
        # Criar tabela se não existir
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS url_products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                brand VARCHAR(200),
                description TEXT,
                images TEXT,
                source_url VARCHAR(500),
                price FLOAT,
                category VARCHAR(200),
                ean VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Buscar produtos
        rows = await conn.fetch("""
            SELECT id, name, brand, description, images, source_url, price, created_at
            FROM url_products 
            ORDER BY created_at DESC 
            LIMIT $1
        """, limit)
        
        products = []
        for row in rows:
            products.append({
                "id": row['id'],
                "name": row['name'],
                "brand": row['brand'],
                "description": row['description'][:100] + "..." if row['description'] and len(row['description']) > 100 else row['description'],
                "images": row['images'],
                "source_url": row['source_url'],
                "price": row['price'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "status": "success",
            "service": "url-extractor",
            "count": len(products),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        await conn.close()

@app.get("/smart-extract")
async def smart_extract(
    url: str = Query(..., description="URL to extract products from"),
    max_products: int = Query(20, description="Maximum products to extract")
):
    """Smart extraction from URL"""
    conn = await get_db_connection()
    try:
        # Criar tabela se não existir
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS url_products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                brand VARCHAR(200),
                description TEXT,
                images TEXT,
                source_url VARCHAR(500),
                price FLOAT,
                category VARCHAR(200),
                ean VARCHAR(50),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = '/'.join(url.split('/')[:3])
            
            # Detectar se é página de produto
            is_product = detect_product_page(soup, url)
            
            processed_products = []
            
            if is_product:
                logger.info(f"Detected product page: {url}")
                product_data = extract_product_data(soup, url)
                if product_data and product_data.get('name'):
                    product_id = await save_product(conn, product_data)
                    if product_id:
                        processed_products.append({
                            'id': product_id,
                            'url': url,
                            'name': product_data['name'],
                            'brand': product_data.get('brand'),
                            'price': product_data.get('price')
                        })
            else:
                logger.info(f"Detected category/listing page: {url}")
                product_links = extract_product_links(soup, base_domain, url)
                logger.info(f"Found {len(product_links)} product links on page")
                
                for product_url in product_links[:max_products]:
                    try:
                        product_data = await extract_from_url(product_url, client, headers)
                        if product_data and product_data.get('name'):
                            product_id = await save_product(conn, product_data)
                            if product_id:
                                processed_products.append({
                                    'id': product_id,
                                    'url': product_url,
                                    'name': product_data['name'],
                                    'brand': product_data.get('brand'),
                                    'price': product_data.get('price')
                                })
                    except Exception as e:
                        logger.error(f"Error processing product {product_url}: {e}")
                        continue
            
            return {
                "status": "success",
                "service": "url-extractor",
                "message": f"Smart extraction completed: {len(processed_products)} products processed",
                "source_url": url,
                "page_type": "product" if is_product else "category/listing",
                "products_processed": len(processed_products),
                "products": processed_products
            }
        
    except Exception as e:
        logger.error(f"Error in smart extraction from {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Smart extraction error: {str(e)}")
    finally:
        await conn.close()

@app.post("/test-scrape")
async def test_scrape(url: str = Query(..., description="URL to test scraping")):
    """Test URL scraping"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_data = extract_product_data(soup, url)
            
            return {
                "status": "success",
                "service": "url-extractor",
                "product_data": product_data
            }
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

# Funções auxiliares
def detect_product_page(soup, url):
    """Detecta se é uma página de produto - otimizado para Cobasi"""
    try:
        indicators = [
            # Padrão específico da Cobasi
            'idsku=' in url.lower(),
            '/p?' in url.lower(),
            # Padrões genéricos
            '/produto/' in url.lower(),
            '/product/' in url.lower(),
            '/p/' in url.lower(),
            '/item/' in url.lower(),
            # Elementos HTML
            soup.select_one('[itemprop="name"]') is not None,
            soup.select_one('[itemprop="price"]') is not None,
            soup.select_one('.product-price') is not None,
            soup.select_one('.add-to-cart') is not None,
            soup.select_one('.comprar') is not None,
            # Elementos específicos da Cobasi
            soup.select_one('[data-testid="product-name"]') is not None,
            soup.select_one('[data-testid="price"]') is not None,
        ]
        return sum(indicators) >= 2
    except:
        return False

def extract_product_links(soup, base_domain, current_url):
    """Extrai links de produtos da página atual - otimizado para Cobasi"""
    try:
        links = []
        
        # Método específico para Cobasi - procurar links com /p?idsku=
        if 'cobasi.com.br' in current_url:
            cobasi_links = soup.find_all('a', href=re.compile(r'/p\?idsku=\d+'))
            logger.info(f"Found {len(cobasi_links)} Cobasi product links")
            
            for link in cobasi_links:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        href = base_domain + href
                    elif not href.startswith('http'):
                        href = urljoin(current_url, href)
                    
                    if href not in links:
                        links.append(href)
        
        # Método genérico para outros sites
        if not links:
            selectors = [
                'a[href*="/produto/"]',
                'a[href*="/product/"]',
                'a[href*="/p/"]',
                'a[href*="/item/"]',
                '.product-item a',
                '.produto a',
                '.card-produto a',
                '.product-card a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        if href.startswith('/'):
                            href = base_domain + href
                        elif not href.startswith('http'):
                            href = urljoin(current_url, href)
                        
                        if href not in links:
                            links.append(href)
        
        return links
    except Exception as e:
        logger.error(f"Error extracting product links: {e}")
        return []

async def extract_from_url(product_url, client, headers):
    """Extrai dados de produto de uma URL específica"""
    try:
        response = await client.get(product_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_product_data(soup, product_url)
    except Exception as e:
        logger.error(f"Error extracting product from {product_url}: {e}")
        return None

def extract_product_data(soup, url):
    """Extrai dados completos do produto - versão otimizada para Cobasi"""
    try:
        data = {
            'source_url': url,
            'name': None,
            'brand': None,
            'price': None,
            'description': None,
            'images': [],
            'category': None,
            'sku': None
        }
        
        # Extrair SKU da URL (específico para Cobasi)
        sku_match = re.search(r'idsku=(\d+)', url)
        if sku_match:
            data['sku'] = sku_match.group(1)
        
        # Nome do produto
        name_selectors = ['h1', '.product-name', '.product-title', '[itemprop="name"]', '[data-testid="product-name"]']
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if len(name) > 5:
                    data['name'] = name
                    break
        
        # Marca - tentar extrair do nome se não encontrar elemento específico
        brand_selectors = ['[itemprop="brand"]', '.product-brand', '.brand-name', '.marca']
        for selector in brand_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    data['brand'] = elem.get('content', '').strip()
                else:
                    data['brand'] = elem.get_text(strip=True)
                break
        
        # Se não encontrou marca, extrair da URL ou nome
        if not data['brand']:
            if data['name']:
                # Primeira palavra do nome geralmente é a marca
                words = data['name'].split()
                if len(words) > 1:
                    data['brand'] = words[0]
            else:
                # Extrair da URL
                domain = url.split('/')[2].replace('www.', '').split('.')[0]
                data['brand'] = domain.upper()
        
        # Preço - melhorado para Cobasi
        price_selectors = [
            '[itemprop="price"]', 
            '.product-price', 
            '.price', 
            '.valor', 
            '.preco',
            '[data-testid="price"]'
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True) if elem.name != 'meta' else elem.get('content', '')
                price_match = re.search(r'(\d+[.,]\d{2})', price_text)
                if price_match:
                    try:
                        data['price'] = float(price_match.group(1).replace(',', '.'))
                        break
                    except:
                        continue
        
        # Se não encontrou preço nos elementos, procurar no texto
        if not data['price']:
            price_texts = soup.find_all(string=re.compile(r'R\$\s*\d+[,.]?\d*'))
            for text in price_texts:
                price_match = re.search(r'R\$\s*([\d.,]+)', text)
                if price_match:
                    try:
                        price_str = price_match.group(1).replace('.', '').replace(',', '.')
                        data['price'] = float(price_str)
                        break
                    except:
                        continue
        
        # Descrição
        desc_selectors = ['[itemprop="description"]', '.product-description', '.description', '.descricao']
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    data['description'] = elem.get('content', '').strip()
                else:
                    desc = elem.get_text(strip=True)
                    if len(desc) > 10:
                        data['description'] = desc[:500]
                break
        
        # Imagens - melhorado para Cobasi
        img_selectors = [
            'img[itemprop="image"]', 
            '.product-image img', 
            '.product-gallery img',
            'img[src*="product"]',
            'img[src*="produto"]'
        ]
        
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs[:3]:
                src = img.get('src') or img.get('data-src')
                if src and 'placeholder' not in src.lower() and 'loading' not in src.lower():
                    if not src.startswith('http'):
                        src = urljoin(url, src)
                    if src not in data['images']:
                        data['images'].append(src)
            if data['images']:
                break
        
        return data
    except Exception as e:
        logger.error(f"Error extracting product data: {e}")
        return None

async def save_product(conn, product_data):
    """Salva produto no banco de dados"""
    try:
        product_id = await conn.fetchval("""
            INSERT INTO url_products (name, brand, description, images, source_url, price, category, ean)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """, 
            product_data.get('name'),
            product_data.get('brand') or 'Unknown',
            product_data.get('description') or '',
            json.dumps(product_data.get('images', [])),
            product_data.get('source_url'),
            product_data.get('price'),
            product_data.get('category'),
            product_data.get('ean')
        )
        
        logger.info(f"Saved product: {product_data.get('name')} (ID: {product_id})")
        return product_id
        
    except Exception as e:
        logger.error(f"Error saving product to DB: {e}")
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)