"""
Sistema de Parsing de Ingredientes e Informações Nutricionais para o SixPet Catalog Engine.

Este módulo implementa funções especializadas para extrair e normalizar:
- Lista de ingredientes de produtos pet
- Tabelas nutricionais de páginas web
- Normalização de unidades nutricionais
"""

import re
from typing import Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class NutritionParser:
    """Parser especializado para ingredientes e informações nutricionais."""
    
    def __init__(self):
        # Ingredientes comuns e suas normalizações
        self.ingredient_aliases = {
            # Proteínas
            'frango': 'frango',
            'chicken': 'frango',
            'pollo': 'frango',
            'carne bovina': 'carne bovina',
            'beef': 'carne bovina',
            'carne': 'carne bovina',
            'cordeiro': 'cordeiro',
            'lamb': 'cordeiro',
            'peixe': 'peixe',
            'fish': 'peixe',
            'salmão': 'salmão',
            'salmon': 'salmão',
            'atum': 'atum',
            'tuna': 'atum',
            
            # Cereais e carboidratos
            'arroz': 'arroz',
            'rice': 'arroz',
            'milho': 'milho',
            'corn': 'milho',
            'trigo': 'trigo',
            'wheat': 'trigo',
            'aveia': 'aveia',
            'oats': 'aveia',
            'cevada': 'cevada',
            'barley': 'cevada',
            'batata': 'batata',
            'potato': 'batata',
            'batata doce': 'batata doce',
            'sweet potato': 'batata doce',
            
            # Vegetais
            'cenoura': 'cenoura',
            'carrot': 'cenoura',
            'ervilha': 'ervilha',
            'pea': 'ervilha',
            'beterraba': 'beterraba',
            'beet': 'beterraba',
            'espinafre': 'espinafre',
            'spinach': 'espinafre',
            
            # Outros
            'óleo': 'óleo',
            'oil': 'óleo',
            'gordura': 'gordura',
            'fat': 'gordura',
            'vitaminas': 'vitaminas',
            'vitamins': 'vitaminas',
            'minerais': 'minerais',
            'minerals': 'minerais',
        }
        
        # Padrões para remoção de percentuais e quantidades
        self.percentage_patterns = [
            r'\([^)]*%[^)]*\)',  # (15%)
            r'\([^)]*\d+[.,]\d*[^)]*\)',  # (1,5g)
            r'\d+[.,]?\d*\s*%',  # 15%
            r'\d+[.,]?\d*\s*g\b',  # 15g
            r'\d+[.,]?\d*\s*mg\b',  # 150mg
            r'\d+[.,]?\d*\s*kg\b',  # 1kg
        ]
        
        # Mapeamento de nutrientes
        self.nutrient_mapping = {
            # Proteína
            'proteína': 'protein',
            'proteina': 'protein',
            'protein': 'protein',
            'proteínas': 'protein',
            'proteinas': 'protein',
            'proteins': 'protein',
            
            # Gordura
            'gordura': 'fat',
            'gorduras': 'fat',
            'fat': 'fat',
            'fats': 'fat',
            'lipídios': 'fat',
            'lipidios': 'fat',
            'lipids': 'fat',
            'extrato etéreo': 'fat',
            
            # Fibra
            'fibra': 'fiber',
            'fibras': 'fiber',
            'fiber': 'fiber',
            'fibre': 'fiber',
            'fibra bruta': 'fiber',
            'crude fiber': 'fiber',
            
            # Umidade
            'umidade': 'moisture',
            'moisture': 'moisture',
            'água': 'moisture',
            'water': 'moisture',
            
            # Cinzas
            'cinzas': 'ash',
            'ash': 'ash',
            'matéria mineral': 'ash',
            'mineral matter': 'ash',
            'resíduo mineral': 'ash',
            
            # Energia
            'energia': 'energy',
            'energy': 'energy',
            'calorias': 'energy',
            'calories': 'energy',
            'kcal': 'energy',
            'energia metabolizável': 'energy',
            'metabolizable energy': 'energy',
            
            # Carboidratos
            'carboidratos': 'carbohydrates',
            'carboidrato': 'carbohydrates',
            'carbohydrates': 'carbohydrates',
            'carbohydrate': 'carbohydrates',
            'extrativo não nitrogenado': 'carbohydrates',
            
            # Cálcio
            'cálcio': 'calcium',
            'calcio': 'calcium',
            'calcium': 'calcium',
            'ca': 'calcium',
            
            # Fósforo
            'fósforo': 'phosphorus',
            'fosforo': 'phosphorus',
            'phosphorus': 'phosphorus',
            'p': 'phosphorus',
        }
        
        # Padrões de unidades
        self.unit_patterns = {
            'percentage': r'(\d+[.,]?\d*)\s*%',
            'grams_per_100g': r'(\d+[.,]?\d*)\s*g\s*/?\s*100\s*g',
            'grams': r'(\d+[.,]?\d*)\s*g\b',
            'milligrams': r'(\d+[.,]?\d*)\s*mg\b',
            'kcal_per_100g': r'(\d+[.,]?\d*)\s*kcal\s*/?\s*100\s*g',
            'kcal': r'(\d+[.,]?\d*)\s*kcal\b',
        }

    def parse_ingredients(self, text: str) -> List[str]:
        """
        Separa e normaliza lista de ingredientes de texto.
        
        Args:
            text: Texto contendo lista de ingredientes
            
        Returns:
            Lista de ingredientes normalizados
            
        Examples:
            >>> parser = NutritionParser()
            >>> parser.parse_ingredients("Frango (15%), arroz, milho, óleo de frango")
            ['frango', 'arroz', 'milho', 'óleo']
            
            >>> parser.parse_ingredients("Chicken meal, rice, corn oil, vitamins")
            ['frango', 'arroz', 'óleo', 'vitaminas']
        """
        if not text or not isinstance(text, str):
            return []
        
        try:
            logger.debug(f"Parsing ingredients from text: {text[:100]}...")
            
            # Limpar texto inicial
            text = text.strip()
            
            # Remover prefixos comuns
            prefixes_to_remove = [
                'ingredientes:', 'ingredients:', 'composição:', 'composition:',
                'lista de ingredientes:', 'ingredient list:', 'contém:', 'contains:'
            ]
            
            text_lower = text.lower()
            for prefix in prefixes_to_remove:
                if text_lower.startswith(prefix):
                    text = text[len(prefix):].strip()
                    break
            
            # Remover percentuais e quantidades entre parênteses
            for pattern in self.percentage_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
            # Separar por vírgulas, ponto e vírgula, ou quebras de linha
            separators = r'[,;]\s*|\n\s*'
            ingredients = re.split(separators, text)
            
            # Processar cada ingrediente
            normalized_ingredients = []
            for ingredient in ingredients:
                ingredient = ingredient.strip()
                if not ingredient:
                    continue
                
                # Remover números e pontos no início (ex: "1. Frango")
                ingredient = re.sub(r'^\d+\.\s*', '', ingredient)
                
                # Remover caracteres especiais no final
                ingredient = re.sub(r'[.,;]+$', '', ingredient)
                
                # Normalizar ingrediente
                normalized = self._normalize_ingredient(ingredient)
                if normalized and normalized not in normalized_ingredients:
                    normalized_ingredients.append(normalized)
            
            logger.info(f"Parsed {len(normalized_ingredients)} ingredients from text")
            return normalized_ingredients
            
        except Exception as e:
            logger.error(f"Error parsing ingredients: {e}")
            return []

    def _normalize_ingredient(self, ingredient: str) -> Optional[str]:
        """
        Normaliza um ingrediente individual.
        
        Args:
            ingredient: Nome do ingrediente bruto
            
        Returns:
            Nome normalizado ou None se inválido
        """
        if not ingredient or len(ingredient.strip()) < 2:
            return None
        
        ingredient = ingredient.lower().strip()
        
        # Verificar aliases diretos
        if ingredient in self.ingredient_aliases:
            return self.ingredient_aliases[ingredient]
        
        # Verificar aliases parciais (contém)
        for alias, normalized in self.ingredient_aliases.items():
            if alias in ingredient or ingredient in alias:
                return normalized
        
        # Se não encontrou alias, retornar capitalizado
        return ingredient.title()

    def parse_nutritional_table(self, html: str) -> Dict[str, Union[float, str]]:
        """
        Extrai tabela nutricional de HTML de páginas de produtos.
        
        Args:
            html: HTML da página do produto
            
        Returns:
            Dicionário com informações nutricionais normalizadas
            
        Examples:
            >>> parser = NutritionParser()
            >>> html = '<table><tr><td>Proteína</td><td>25%</td></tr></table>'
            >>> result = parser.parse_nutritional_table(html)
            >>> result['protein']
            25.0
        """
        if not html or not isinstance(html, str):
            return {}
        
        try:
            logger.debug(f"Parsing nutritional table from HTML ({len(html)} chars)")
            
            soup = BeautifulSoup(html, 'html.parser')
            nutritional_info = {}
            
            # Estratégias de extração
            strategies = [
                self._extract_from_table,
                self._extract_from_divs,
                self._extract_from_text,
            ]
            
            for strategy in strategies:
                try:
                    result = strategy(soup)
                    if result:
                        nutritional_info.update(result)
                except Exception as e:
                    logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                    continue
            
            # Normalizar unidades para g/100g
            normalized_info = self._normalize_nutritional_units(nutritional_info)
            
            logger.info(f"Extracted {len(normalized_info)} nutritional values")
            return normalized_info
            
        except Exception as e:
            logger.error(f"Error parsing nutritional table: {e}")
            return {}

    def _extract_from_table(self, soup: BeautifulSoup) -> Dict[str, Union[float, str]]:
        """Extrai dados de tabelas HTML."""
        nutritional_info = {}
        
        # Procurar tabelas com conteúdo nutricional
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    nutrient_cell = cells[0].get_text(strip=True)
                    value_cell = cells[1].get_text(strip=True)
                    
                    # Normalizar nome do nutriente
                    normalized_nutrient = self._normalize_nutrient_name(nutrient_cell)
                    if normalized_nutrient:
                        # Extrair valor numérico
                        value = self._extract_numeric_value(value_cell)
                        if value is not None:
                            nutritional_info[normalized_nutrient] = value
        
        return nutritional_info

    def _extract_from_divs(self, soup: BeautifulSoup) -> Dict[str, Union[float, str]]:
        """Extrai dados de divs com classes relacionadas a nutrição."""
        nutritional_info = {}
        
        # Seletores comuns para informações nutricionais
        selectors = [
            '.nutrition-info',
            '.nutritional-info',
            '.nutrition-table',
            '.nutrition-facts',
            '.product-nutrition',
            '[class*="nutri"]',
            '[class*="nutrition"]',
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            
            for element in elements:
                text = element.get_text()
                # Usar regex para extrair pares nutriente-valor
                matches = re.findall(
                    r'([a-záàâãéêíóôõúç\s]+)[\s:]+(\d+[.,]?\d*)\s*([%gm])',
                    text,
                    re.IGNORECASE
                )
                
                for match in matches:
                    nutrient_name, value_str, unit = match
                    normalized_nutrient = self._normalize_nutrient_name(nutrient_name)
                    
                    if normalized_nutrient:
                        try:
                            value = float(value_str.replace(',', '.'))
                            nutritional_info[normalized_nutrient] = value
                        except ValueError:
                            continue
        
        return nutritional_info

    def _extract_from_text(self, soup: BeautifulSoup) -> Dict[str, Union[float, str]]:
        """Extrai dados do texto geral da página."""
        nutritional_info = {}
        
        # Obter todo o texto da página
        text = soup.get_text()
        
        # Padrões para capturar informações nutricionais
        patterns = [
            # Proteína: 25%
            r'(proteína|protein)[\s:]+(\d+[.,]?\d*)\s*%',
            # Gordura 15%
            r'(gordura|fat)[\s:]+(\d+[.,]?\d*)\s*%',
            # Fibra: 3%
            r'(fibra|fiber)[\s:]+(\d+[.,]?\d*)\s*%',
            # Umidade 10%
            r'(umidade|moisture)[\s:]+(\d+[.,]?\d*)\s*%',
            # Cinzas: 8%
            r'(cinzas|ash)[\s:]+(\d+[.,]?\d*)\s*%',
            # Energia: 3500 kcal
            r'(energia|energy)[\s:]+(\d+[.,]?\d*)\s*kcal',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                nutrient_name, value_str = match
                normalized_nutrient = self._normalize_nutrient_name(nutrient_name)
                
                if normalized_nutrient:
                    try:
                        value = float(value_str.replace(',', '.'))
                        nutritional_info[normalized_nutrient] = value
                    except ValueError:
                        continue
        
        return nutritional_info

    def _normalize_nutrient_name(self, name: str) -> Optional[str]:
        """
        Normaliza nome de nutriente.
        
        Args:
            name: Nome bruto do nutriente
            
        Returns:
            Nome normalizado ou None se não reconhecido
        """
        if not name:
            return None
        
        name = name.lower().strip()
        
        # Remover caracteres especiais
        name = re.sub(r'[^\w\s]', '', name)
        
        # Verificar mapeamento
        return self.nutrient_mapping.get(name)

    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extrai valor numérico de texto.
        
        Args:
            text: Texto contendo valor numérico
            
        Returns:
            Valor numérico ou None se não encontrado
        """
        if not text:
            return None
        
        # Tentar diferentes padrões de números
        patterns = [
            r'(\d+[.,]\d+)',  # 25.5 ou 25,5
            r'(\d+)',  # 25
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1).replace(',', '.'))
                except ValueError:
                    continue
        
        return None

    def _normalize_nutritional_units(self, nutritional_info: Dict[str, Union[float, str]]) -> Dict[str, float]:
        """
        Normaliza unidades nutricionais para g/100g (exceto energia que fica em kcal/100g).
        
        Args:
            nutritional_info: Dicionário com valores brutos
            
        Returns:
            Dicionário com valores normalizados
        """
        normalized = {}
        
        for nutrient, value in nutritional_info.items():
            if not isinstance(value, (int, float)):
                continue
            
            # Energia mantém em kcal/100g
            if nutrient == 'energy':
                normalized[nutrient] = float(value)
            else:
                # Outros nutrientes: assumir que % = g/100g
                # Se valor > 100, assumir que está em mg e converter para g
                if value > 100:
                    normalized[nutrient] = round(value / 1000, 2)  # mg para g
                else:
                    normalized[nutrient] = float(value)  # % ou g/100g
        
        return normalized


# Funções de conveniência para compatibilidade
def parse_ingredients(text: str) -> List[str]:
    """
    Função de conveniência para parsing de ingredientes.
    
    Args:
        text: Texto contendo lista de ingredientes
        
    Returns:
        Lista de ingredientes normalizados
    """
    parser = NutritionParser()
    return parser.parse_ingredients(text)


def parse_nutritional_table(html: str) -> Dict[str, Union[float, str]]:
    """
    Função de conveniência para parsing de tabela nutricional.
    
    Args:
        html: HTML da página do produto
        
    Returns:
        Dicionário com informações nutricionais normalizadas
    """
    parser = NutritionParser()
    return parser.parse_nutritional_table(html)


# Instância global para reutilização
nutrition_parser = NutritionParser()