"""
Serviço de enriquecimento web para produtos
Busca informações adicionais na internet para produtos de catálogos
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional
from app.logger import logger
from urllib.parse import quote_plus
import json

class WebEnrichmentService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        }
        
        # Sites para busca de enriquecimento
        self.search_sites = [
            'https://www.cobasi.com.br',
            'https://www.petlove.com.br',
            'https://www.petz.com.br'
        ]
    
    async def enrich_product(self, product_data: Dict) -> Dict:
        """Enriquece produto com dados da web"""
        logger.info(f"🌐 Iniciando enriquecimento web para: {product_data.get('name')}")
        
        try:
            # Buscar informações em sites de pet
            enrichment_data = await self.search_product_info(
                product_data.get('name', ''),
                product_data.get('brand', '')
            )
            
            if enrichment_data:
                # Mesclar dados encontrados com dados originais
                enriched_product = self.merge_enrichment_data(product_data, enrichment_data)
                enriched_product['is_enriched'] = True
                enriched_product['enrichment_source'] = enrichment_data.get('source_url', 'web_search')
                
                logger.info(f"✅ Produto enriquecido com sucesso: {enriched_product.get('name')}")
                return enriched_product
            else:
                # Não encontrou dados adicionais
                product_data['is_enriched'] = False
                product_data['enrichment_source'] = 'web_search_no_results'
                
                logger.info(f"⚠️ Nenhum dado adicional encontrado para: {product_data.get('name')}")
                return product_data
                
        except Exception as e:
            logger.error(f"❌ Erro no enriquecimento web: {e}")
            product_data['is_enriched'] = False
            product_data['enrichment_source'] = f'web_search_error: {str(e)}'
            return product_data
    
    async def search_product_info(self, product_name: str, brand: str = None) -> Optional[Dict]:
        """Busca informações do produto em sites de pet"""
        
        # Construir termos de busca
        search_terms = self.build_search_terms(product_name, brand)
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for search_term in search_terms:
                logger.info(f"🔍 Buscando: {search_term}")
                
                # Tentar buscar na Cobasi primeiro (dados mais ricos)
                cobasi_result = await self.search_cobasi(session, search_term)
                if cobasi_result:
                    return cobasi_result
                
                # Se não encontrou na Cobasi, tentar outros sites
                for site in self.search_sites[1:]:  # Pular Cobasi que já foi testada
                    result = await self.search_generic_site(session, site, search_term)
                    if result:
                        return result
                
                # Pequena pausa entre buscas
                await asyncio.sleep(1)
        
        return None
    
    def build_search_terms(self, product_name: str, brand: str = None) -> List[str]:
        """Constrói termos de busca otimizados"""
        terms = []
        
        if not product_name:
            return terms
        
        # Limpar nome do produto
        clean_name = re.sub(r'[^\w\s]', ' ', product_name)
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # Termo 1: Nome completo
        terms.append(clean_name)
        
        # Termo 2: Nome + marca (se disponível)
        if brand:
            terms.append(f"{brand} {clean_name}")
        
        # Termo 3: Palavras-chave principais
        keywords = self.extract_keywords(clean_name)
        if len(keywords) >= 2:
            terms.append(' '.join(keywords[:3]))  # Top 3 keywords
        
        # Termo 4: Apenas marca + tipo de produto (se identificável)
        if brand:
            product_type = self.identify_product_type(clean_name)
            if product_type:
                terms.append(f"{brand} {product_type}")
        
        return terms[:3]  # Máximo 3 termos para não sobrecarregar
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave importantes do texto"""
        # Palavras importantes para produtos pet
        important_words = [
            'ração', 'racao', 'petisco', 'snack', 'biscoito',
            'frango', 'carne', 'peixe', 'salmão', 'cordeiro',
            'adulto', 'filhote', 'senior', 'puppy', 'kitten',
            'pequeno', 'medio', 'grande', 'mini', 'maxi',
            'premium', 'super', 'natural', 'organic'
        ]
        
        words = text.lower().split()
        keywords = []
        
        for word in words:
            if len(word) > 3 and (word in important_words or word.isalpha()):
                keywords.append(word)
        
        return keywords
    
    def identify_product_type(self, text: str) -> Optional[str]:
        """Identifica tipo de produto"""
        text_lower = text.lower()
        
        if 'ração' in text_lower or 'racao' in text_lower:
            return 'ração'
        elif 'petisco' in text_lower or 'snack' in text_lower:
            return 'petisco'
        elif 'biscoito' in text_lower:
            return 'biscoito'
        
        return None
    
    async def search_cobasi(self, session: aiohttp.ClientSession, search_term: str) -> Optional[Dict]:
        """Busca específica na Cobasi"""
        try:
            # URL de busca da Cobasi
            search_url = f"https://www.cobasi.com.br/busca?q={quote_plus(search_term)}"
            
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Procurar primeiro produto nos resultados
                    product_links = soup.find_all('a', href=re.compile(r'/p\?idsku=\d+'))
                    
                    if product_links:
                        first_product_url = product_links[0].get('href')
                        if not first_product_url.startswith('http'):
                            first_product_url = 'https://www.cobasi.com.br' + first_product_url
                        
                        # Extrair dados do produto
                        product_data = await self.extract_cobasi_product_data(session, first_product_url)
                        if product_data:
                            product_data['source_url'] = first_product_url
                            return product_data
            
        except Exception as e:
            logger.error(f"❌ Erro na busca Cobasi: {e}")
        
        return None
    
    async def extract_cobasi_product_data(self, session: aiohttp.ClientSession, product_url: str) -> Optional[Dict]:
        """Extrai dados detalhados de produto da Cobasi"""
        try:
            async with session.get(product_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    text_content = soup.get_text()
                    
                    # Extrair dados usando padrões da Cobasi
                    data = {}
                    
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
                            data[key] = match.group(1).strip()
                    
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
                            data[key] = match.group(1)
                    
                    # Composição
                    comp_match = re.search(r'Composição Básica\s*([^A-Z]{100,500})', text_content, re.IGNORECASE | re.DOTALL)
                    if comp_match:
                        data['composicao_completa'] = comp_match.group(1).strip()
                    
                    # Descrição
                    desc_match = re.search(r'Detalhes do produto\s*([^A-Z]{50,200})', text_content, re.IGNORECASE | re.DOTALL)
                    if desc_match:
                        data['descricao_completa'] = desc_match.group(1).strip()
                    
                    return data if data else None
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados da Cobasi: {e}")
        
        return None
    
    async def search_generic_site(self, session: aiohttp.ClientSession, site_url: str, search_term: str) -> Optional[Dict]:
        """Busca genérica em outros sites"""
        # TODO: Implementar busca em outros sites (Petlove, Petz, etc.)
        # Por enquanto, retorna None
        return None
    
    def merge_enrichment_data(self, original_data: Dict, enrichment_data: Dict) -> Dict:
        """Mescla dados originais com dados de enriquecimento"""
        merged = original_data.copy()
        
        # Campos que podem ser enriquecidos (só sobrescrever se original estiver vazio)
        enrichable_fields = [
            'porte', 'tipo_produto', 'peso_produto', 'sabor', 'idade_pet',
            'linha_produto', 'proteina_bruta', 'fosforo', 'calcio_min',
            'energia_metabolizavel', 'composicao_completa', 'descricao_completa'
        ]
        
        for field in enrichable_fields:
            if enrichment_data.get(field) and not merged.get(field):
                merged[field] = enrichment_data[field]
        
        # Adicionar dados de enriquecimento aos dados brutos
        if 'raw_data' not in merged:
            merged['raw_data'] = {}
        
        merged['raw_data']['enrichment_data'] = enrichment_data
        
        return merged