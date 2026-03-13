from fastapi import APIRouter, HTTPException, Depends, Query
from app.logger import logger
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from typing import Optional

router = APIRouter()

# ✅ 1º: ROTAS ESTÁTICAS SEMPRE PRIMEIRO (seguindo a documentação)
@router.get("/health")
async def sitemap_health():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}

@router.get("/debug")
async def debug_routes():
    """Debug: endpoint de teste"""
    return {"status": "debug", "message": "Debug endpoint is working"}

@router.get("/products")
async def list_extracted_products(limit: int = Query(10, description="Número máximo de produtos"), db: Session = Depends(get_db)):
    """Lista os produtos extraídos de URLs"""
    try:
        # Criar tabela se não existir
        db.execute(text("""
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
        """))
        db.commit()
        
        result = db.execute(text("""
            SELECT id, name, brand, description, images, source_url, price, created_at
            FROM url_products 
            ORDER BY created_at DESC 
            LIMIT :limit
        """), {'limit': limit})
        
        products = []
        for row in result:
            products.append({
                "id": row[0],
                "name": row[1],
                "brand": row[2],
                "description": row[3][:100] + "..." if row[3] and len(row[3]) > 100 else row[3],
                "images": row[4],
                "source_url": row[5],
                "price": row[6],
                "created_at": row[7].isoformat() if row[7] else None
            })
        
        return {
            "status": "success",
            "count": len(products),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# ✅ URL como query parameter (recomendado pela documentação)
@router.get("/smart-extract")
async def smart_extract_products(
    url: str = Query(..., description="URL para extrair produtos"),
    max_products: int = Query(20, description="Número máximo de produtos a extrair"),
    db: Session = Depends(get_db)
):
    """
    Extração inteligente: detecta automaticamente se é produto ou categoria
    """
    try:
        # Criar tabela se não existir
        db.execute(text("""
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
        """))
        db.commit()
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            base_domain = '/'.join(url.split('/')[:3])
            
            # Detectar se é página de produto
            is_product = detect_product_page_simple(soup, url)
            
            processed_products = []
            
            if is_product:
                logger.info(f"Detected product page: {url}")
                product_data = extract_product_data_complete(soup, url)
                if product_data and product_data.get('name'):
                    product_id = save_product_db(db, product_data)
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
                product_links = extract_links_simple(soup, base_domain, url)
                logger.info(f"Found {len(product_links)} product links on page")
                
                for product_url in product_links[:max_products]:
                    try:
                        product_data = await extract_from_url_simple(product_url, client, headers)
                        if product_data and product_data.get('name'):
                            product_id = save_product_db(db, product_data)
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
            
            db.commit()
            
            return {
                "status": "success",
                "message": f"Smart extraction completed: {len(processed_products)} products processed",
                "source_url": url,
                "page_type": "product" if is_product else "category/listing",
                "products_processed": len(processed_products),
                "products": processed_products
            }
        
    except Exception as e:
        logger.error(f"Error in smart extraction from {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Smart extraction error: {str(e)}")

@router.post("/test-scrape")
async def test_scrape_url(url: str = Query(..., description="URL para testar extração")):
    """
    Testa a extração de dados de uma URL específica
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_data = {
                'source_url': url,
                'name': None,
                'brand': None,
                'price': None,
                'description': None,
                'images': []
            }
            
            # Extrair nome do produto
            name_selectors = ['h1', '.product-name', '.product-title', '[itemprop="name"]']
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product_data['name'] = elem.get_text(strip=True)
                    break
            
            # Extrair marca
            brand_selectors = ['[itemprop="brand"]', '.product-brand', '.brand-name']
            for selector in brand_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if elem.name == 'meta':
                        product_data['brand'] = elem.get('content', '').strip()
                    else:
                        product_data['brand'] = elem.get_text(strip=True)
                    break
            
            # Extrair preço
            price_selectors = ['[itemprop="price"]', '.product-price', '.price']
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True) if elem.name != 'meta' else elem.get('content', '')
                    price_match = re.search(r'(\d+[.,]\d{2})', price_text)
                    if price_match:
                        try:
                            product_data['price'] = float(price_match.group(1).replace(',', '.'))
                            break
                        except:
                            continue
            
            # Extrair descrição
            desc_selectors = ['[itemprop="description"]', '.product-description', '.description']
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if elem.name == 'meta':
                        product_data['description'] = elem.get('content', '').strip()
                    else:
                        product_data['description'] = elem.get_text(strip=True)[:500]
                    break
            
            # Extrair imagens
            img_selectors = ['img[itemprop="image"]', '.product-image img', '.product-gallery img']
            for selector in img_selectors:
                imgs = soup.select(selector)
                for img in imgs[:3]:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if not src.startswith('http'):
                            src = urljoin(url, src)
                        product_data['images'].append(src)
                if product_data['images']:
                    break
            
            return {
                "status": "success",
                "product_data": product_data
            }
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

# ✅ ÚLTIMO: Rotas dinâmicas com path param (se necessário)
# Neste caso, não precisamos de rotas dinâmicas com path param

# Funções auxiliares com nomes únicos
def detect_product_page_simple(soup, url):
    """Detecta se é uma página de produto"""
    try:
        indicators = [
            '/produto/' in url.lower(),
            '/product/' in url.lower(),
            '/p/' in url.lower(),
            '/item/' in url.lower(),
            soup.select_one('[itemprop="name"]') is not None,
            soup.select_one('[itemprop="price"]') is not None,
            soup.select_one('.product-price') is not None,
            soup.select_one('.add-to-cart') is not None,
            soup.select_one('.comprar') is not None,
        ]
        return sum(indicators) >= 2
    except:
        return False

def extract_links_simple(soup, base_domain, current_url):
    """Extrai links de produtos da página atual"""
    try:
        links = []
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
    except:
        return []

async def extract_from_url_simple(product_url, client, headers):
    """Extrai dados de produto de uma URL específica"""
    try:
        response = await client.get(product_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return extract_product_data_complete(soup, product_url)
    except Exception as e:
        logger.error(f"Error extracting product from {product_url}: {e}")
        return None

def extract_product_data_complete(soup, url):
    """Extrai dados completos do produto"""
    try:
        data = {
            'source_url': url,
            'name': None,
            'brand': None,
            'price': None,
            'description': None,
            'images': [],
            'category': None,
            'ean': None
        }
        
        # Nome do produto
        name_selectors = ['h1', '.product-name', '.product-title', '[itemprop="name"]']
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                name = elem.get_text(strip=True)
                if len(name) > 5:
                    data['name'] = name
                    break
        
        # Marca
        brand_selectors = ['[itemprop="brand"]', '.product-brand', '.brand-name']
        for selector in brand_selectors:
            elem = soup.select_one(selector)
            if elem:
                if elem.name == 'meta':
                    data['brand'] = elem.get('content', '').strip()
                else:
                    data['brand'] = elem.get_text(strip=True)
                break
        
        if not data['brand']:
            domain = url.split('/')[2].replace('www.', '').split('.')[0]
            data['brand'] = domain.upper()
        
        # Preço
        price_selectors = ['[itemprop="price"]', '.product-price', '.price', '.valor', '.preco']
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
        
        # Descrição
        desc_selectors = ['[itemprop="description"]', '.product-description', '.description']
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
        
        # Imagens
        img_selectors = ['img[itemprop="image"]', '.product-image img', '.product-gallery img']
        for selector in img_selectors:
            imgs = soup.select(selector)
            for img in imgs[:3]:
                src = img.get('src') or img.get('data-src')
                if src and 'placeholder' not in src.lower():
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

def save_product_db(db, product_data):
    """Salva produto no banco de dados"""
    try:
        result = db.execute(text("""
            INSERT INTO url_products (name, brand, description, images, source_url, price, category, ean)
            VALUES (:name, :brand, :description, :images, :source_url, :price, :category, :ean)
            RETURNING id
        """), {
            'name': product_data.get('name'),
            'brand': product_data.get('brand') or 'Unknown',
            'description': product_data.get('description') or '',
            'images': str(product_data.get('images', [])),
            'source_url': product_data.get('source_url'),
            'price': product_data.get('price'),
            'category': product_data.get('category'),
            'ean': product_data.get('ean')
        })
        
        product_id = result.scalar()
        logger.info(f"Saved product: {product_data.get('name')} (ID: {product_id})")
        return product_id
        
    except Exception as e:
        logger.error(f"Error saving product to DB: {e}")
        return None