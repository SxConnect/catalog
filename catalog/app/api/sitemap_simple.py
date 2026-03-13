from fastapi import APIRouter, HTTPException
from app.logger import logger
import httpx
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

router = APIRouter()

@router.post("/test-scrape")
async def test_scrape_url(url: str):
    """
    Testa a extração de dados de uma URL específica
    Útil para verificar se o scraping está funcionando
    """
    try:
        # Fazer request direto
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrair dados básicos
            product_data = {
                'source_url': url,
                'name': None,
                'brand': None,
                'price': None,
                'description': None,
                'category': None,
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
                    # Extrair número do preço
                    price_match = re.search(r'(\d+[.,]\d{2})', price_text)
                    if price_match:
                        product_data['price'] = float(price_match.group(1).replace(',', '.'))
                        break
            
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
                for img in imgs[:3]:  # Máximo 3 imagens
                    src = img.get('src') or img.get('data-src')
                    if src:
                        if not src.startswith('http'):
                            src = urljoin(url, src)
                        product_data['images'].append(src)
                if product_data['images']:
                    break
            
            if not product_data['name']:
                raise HTTPException(status_code=404, detail="Could not extract product name from URL")
            
            return {
                "status": "success",
                "product_data": product_data
            }
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")

@router.get("/health")
async def sitemap_health():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}