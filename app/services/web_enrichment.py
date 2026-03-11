import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re
from app.logger import logger
from app.utils.retry import retry_web_scraping
from app.monitoring.metrics import monitor_scraping, monitor_enrichment
from app.services.nutrition_parser import nutrition_parser
import asyncio

class WebEnrichmentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def search_google(self, query: str) -> List[str]:
        """Busca URLs no Google (simulado - use Google Custom Search API em produção)"""
        try:
            # Em produção, usar Google Custom Search API
            # Por enquanto, retorna URLs conhecidas de pet shops
            pet_sites = [
                f"https://www.petlove.com.br/busca?q={query.replace(' ', '+')}",
                f"https://www.petz.com.br/busca?q={query.replace(' ', '+')}",
                f"https://www.cobasi.com.br/busca?q={query.replace(' ', '+')}",
            ]
            return pet_sites
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    @retry_web_scraping(max_attempts=5)
    @monitor_scraping
    async def scrape_product_page(self, url: str) -> Dict:
        """
        Extrai dados de uma página de produto com retry automático e circuit breaker.
        
        Args:
            url: URL da página do produto
            
        Returns:
            Dicionário com dados extraídos da página
        """
        try:
            logger.debug(f"Scraping product page: {url}")
            response = await self.client.get(url, headers=self.headers)
            response.raise_for_status()  # Levanta exceção para status HTTP de erro
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {}
            
            # Tentar extrair preço
            price_patterns = [
                r'R\$\s*(\d+[.,]\d{2})',
                r'(\d+[.,]\d{2})\s*reais',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, response.text)
                if match:
                    data['price'] = match.group(1).replace(',', '.')
                    break
            
            # Tentar extrair descrição
            desc_selectors = [
                'div.product-description',
                'div.description',
                'div[itemprop="description"]',
                'meta[name="description"]',
            ]
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    data['description'] = elem.get_text(strip=True)[:500]
                    break
            
            # Tentar extrair imagens
            img_selectors = [
                'img.product-image',
                'img[itemprop="image"]',
                'div.product-gallery img',
            ]
            images = []
            for selector in img_selectors:
                imgs = soup.select(selector)
                for img in imgs[:3]:  # Máximo 3 imagens
                    src = img.get('src') or img.get('data-src')
                    if src and src.startswith('http'):
                        images.append(src)
            data['images'] = images
            
            # Tentar extrair peso/dimensões
            weight_pattern = r'(\d+[.,]?\d*)\s*(kg|g|gramas|quilos)'
            match = re.search(weight_pattern, response.text, re.IGNORECASE)
            if match:
                data['weight'] = f"{match.group(1)} {match.group(2)}"
            
            # Tentar extrair ingredientes
            ingredients_patterns = [
                r'ingredientes?[:\s]+([^.]+)',
                r'composição[:\s]+([^.]+)',
                r'ingredients?[:\s]+([^.]+)',
            ]
            
            for pattern in ingredients_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    ingredients_text = match.group(1).strip()
                    if len(ingredients_text) > 10:  # Filtrar matches muito curtos
                        data['ingredients_text'] = ingredients_text[:500]  # Limitar tamanho
                        break
            
            # Tentar extrair informações nutricionais do HTML
            try:
                nutritional_info = nutrition_parser.parse_nutritional_table(response.text)
                if nutritional_info:
                    data['nutritional_info'] = nutritional_info
            except Exception as e:
                logger.debug(f"Failed to parse nutritional info from {url}: {e}")
            
            logger.info(f"Successfully scraped data from {url}: {len(data)} fields")
            return data
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            raise  # Re-raise para que o retry funcione
    
    @monitor_enrichment
    async def search_product(
        self, 
        product_name: str, 
        brand: str,
        ean: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Busca informações do produto na web
        
        Retorna dados enriquecidos:
        - description: Descrição completa
        - images: Lista de URLs de imagens
        - price: Preço médio encontrado
        - weight: Peso do produto
        - ingredients: Ingredientes (se disponível)
        - nutritional_info: Info nutricional
        """
        try:
            logger.info(f"Enriching product: {product_name} - {brand}")
            
            # Construir query de busca
            query = f"{product_name} {brand}"
            if ean:
                query += f" {ean}"
            query += " pet"
            
            # Buscar URLs
            urls = await self.search_google(query)
            
            # Scrape das primeiras 3 URLs
            enriched_data = {
                "additional_images": [],
                "full_description": "",
                "price_avg": None,
                "weight": None,
                "ean_confirmed": ean,
                "sources": [],
                "ingredients": [],
                "nutritional_info": {}
            }
            
            prices = []
            descriptions = []
            
            for url in urls[:3]:
                data = await self.scrape_product_page(url)
                
                if data.get('price'):
                    try:
                        prices.append(float(data['price']))
                    except:
                        pass
                
                if data.get('description'):
                    descriptions.append(data['description'])
                
                if data.get('images'):
                    enriched_data['additional_images'].extend(data['images'])
                
                if data.get('weight') and not enriched_data['weight']:
                    enriched_data['weight'] = data['weight']
                
                # Processar ingredientes
                if data.get('ingredients_text'):
                    try:
                        ingredients = nutrition_parser.parse_ingredients(data['ingredients_text'])
                        if ingredients:
                            enriched_data['ingredients'].extend(ingredients)
                    except Exception as e:
                        logger.debug(f"Failed to parse ingredients: {e}")
                
                # Consolidar informações nutricionais
                if data.get('nutritional_info'):
                    enriched_data['nutritional_info'].update(data['nutritional_info'])
                
                enriched_data['sources'].append(url)
            
            # Calcular preço médio
            if prices:
                enriched_data['price_avg'] = sum(prices) / len(prices)
            
            # Consolidar descrições
            if descriptions:
                enriched_data['full_description'] = max(descriptions, key=len)
            
            # Remover duplicatas de imagens
            enriched_data['additional_images'] = list(set(enriched_data['additional_images']))[:5]
            
            # Remover duplicatas de ingredientes
            if enriched_data['ingredients']:
                enriched_data['ingredients'] = list(set(enriched_data['ingredients']))
            
            logger.info(f"Enrichment completed: {len(enriched_data['additional_images'])} images, "
                       f"price: {enriched_data['price_avg']}, "
                       f"{len(enriched_data['ingredients'])} ingredients, "
                       f"{len(enriched_data['nutritional_info'])} nutritional values")
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Web enrichment error: {e}")
            return None
    
    def search_product_sync(self, product_name: str, brand: str, ean: Optional[str] = None) -> Optional[Dict]:
        """Versão síncrona para compatibilidade"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.search_product(product_name, brand, ean))
    
    async def close(self):
        await self.client.aclose()
    
    def close_sync(self):
        """Versão síncrona do close"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.close())
