import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from app.logger import logger
import asyncio
import re

class SitemapService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def fetch_sitemap(self, sitemap_url: str) -> List[Dict]:
        """
        Busca e parseia o sitemap.xml
        Retorna lista de URLs com metadados
        """
        try:
            logger.info(f"Fetching sitemap: {sitemap_url}")
            response = await self.client.get(sitemap_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Namespace do sitemap
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            urls = []
            for url_elem in root.findall('sm:url', ns):
                loc = url_elem.find('sm:loc', ns)
                lastmod = url_elem.find('sm:lastmod', ns)
                priority = url_elem.find('sm:priority', ns)
                changefreq = url_elem.find('sm:changefreq', ns)
                
                if loc is not None:
                    urls.append({
                        'url': loc.text,
                        'lastmod': lastmod.text if lastmod is not None else None,
                        'priority': priority.text if priority is not None else None,
                        'changefreq': changefreq.text if changefreq is not None else None
                    })
            
            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            logger.error(f"Error fetching sitemap: {e}")
            return []
    
    async def scrape_product_page(self, url: str) -> Optional[Dict]:
        """
        Extrai dados de produto de uma página específica
        """
        try:
            logger.info(f"Scraping product: {url}")
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            product_data = {
                'source_url': url,
                'name': None,
                'brand': None,
                'ean': None,
                'price': None,
                'description': None,
                'category': None,
                'images': [],
                'specifications': {}
            }
            
            # Extrair nome do produto
            name_selectors = [
                'h1.product-name',
                'h1[itemprop="name"]',
                'h1.product-title',
                '.product-name',
                'h1'
            ]
            for selector in name_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product_data['name'] = elem.get_text(strip=True)
                    break
            
            # Extrair marca
            brand_selectors = [
                '[itemprop="brand"]',
                '.product-brand',
                '.brand-name',
                'meta[property="product:brand"]'
            ]
            for selector in brand_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if elem.name == 'meta':
                        product_data['brand'] = elem.get('content', '').strip()
                    else:
                        product_data['brand'] = elem.get_text(strip=True)
                    break
            
            # Extrair EAN/GTIN
            ean_patterns = [
                r'EAN[:\s]*(\d{13})',
                r'GTIN[:\s]*(\d{13})',
                r'Código de barras[:\s]*(\d{13})',
                r'"gtin13"[:\s]*"(\d{13})"',
                r'"ean"[:\s]*"(\d{13})"'
            ]
            for pattern in ean_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    product_data['ean'] = match.group(1)
                    break
            
            # Extrair preço
            price_selectors = [
                '[itemprop="price"]',
                '.product-price',
                '.price',
                'meta[property="product:price:amount"]'
            ]
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if elem.name == 'meta':
                        price_text = elem.get('content', '')
                    else:
                        price_text = elem.get_text(strip=True)
                    
                    # Extrair número do preço
                    price_match = re.search(r'(\d+[.,]\d{2})', price_text)
                    if price_match:
                        product_data['price'] = float(price_match.group(1).replace(',', '.'))
                        break
            
            # Extrair descrição
            desc_selectors = [
                '[itemprop="description"]',
                '.product-description',
                '.description',
                'meta[name="description"]'
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    if elem.name == 'meta':
                        product_data['description'] = elem.get('content', '').strip()
                    else:
                        product_data['description'] = elem.get_text(strip=True)[:1000]
                    break
            
            # Extrair categoria
            category_selectors = [
                '.breadcrumb',
                '[itemprop="category"]',
                '.product-category'
            ]
            for selector in category_selectors:
                elem = soup.select_one(selector)
                if elem:
                    product_data['category'] = elem.get_text(strip=True)
                    break
            
            # Extrair imagens
            img_selectors = [
                'img[itemprop="image"]',
                '.product-image img',
                '.product-gallery img',
                'img.zoom'
            ]
            for selector in img_selectors:
                imgs = soup.select(selector)
                for img in imgs[:5]:  # Máximo 5 imagens
                    src = img.get('src') or img.get('data-src') or img.get('data-zoom-image')
                    if src:
                        if not src.startswith('http'):
                            # Construir URL absoluta
                            from urllib.parse import urljoin
                            src = urljoin(url, src)
                        product_data['images'].append(src)
                if product_data['images']:
                    break
            
            # Remover duplicatas de imagens
            product_data['images'] = list(dict.fromkeys(product_data['images']))
            
            # Extrair especificações (peso, dimensões, etc)
            spec_patterns = {
                'weight': r'Peso[:\s]*(\d+[.,]?\d*)\s*(kg|g|gramas|quilos)',
                'volume': r'Volume[:\s]*(\d+[.,]?\d*)\s*(ml|l|litros)',
                'dimensions': r'Dimensões[:\s]*([\d\s,x]+)\s*(cm|mm)'
            }
            for key, pattern in spec_patterns.items():
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    product_data['specifications'][key] = match.group(0)
            
            # Validar se extraiu dados mínimos
            if not product_data['name']:
                logger.warning(f"Could not extract product name from {url}")
                return None
            
            logger.info(f"Successfully scraped: {product_data['name']}")
            return product_data
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def process_sitemap(
        self, 
        sitemap_url: str,
        url_filter: Optional[str] = None,
        max_products: Optional[int] = None
    ) -> List[Dict]:
        """
        Processa sitemap completo e extrai dados de produtos
        
        Args:
            sitemap_url: URL do sitemap.xml
            url_filter: Filtro regex para URLs (ex: '/produto/')
            max_products: Limite máximo de produtos a processar
        """
        # Buscar URLs do sitemap
        sitemap_urls = await self.fetch_sitemap(sitemap_url)
        
        if not sitemap_urls:
            return []
        
        # Filtrar URLs se necessário
        if url_filter:
            pattern = re.compile(url_filter)
            sitemap_urls = [u for u in sitemap_urls if pattern.search(u['url'])]
            logger.info(f"Filtered to {len(sitemap_urls)} URLs matching pattern")
        
        # Limitar quantidade se especificado
        if max_products:
            sitemap_urls = sitemap_urls[:max_products]
        
        # Processar URLs em lotes para não sobrecarregar
        batch_size = 10
        products = []
        
        for i in range(0, len(sitemap_urls), batch_size):
            batch = sitemap_urls[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(sitemap_urls)-1)//batch_size + 1}")
            
            # Processar batch em paralelo
            tasks = [self.scrape_product_page(item['url']) for item in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict) and result:
                    products.append(result)
            
            # Pequeno delay entre batches
            await asyncio.sleep(1)
        
        logger.info(f"Successfully extracted {len(products)} products from sitemap")
        return products
    
    async def close(self):
        await self.client.aclose()
