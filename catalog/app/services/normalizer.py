"""
Serviço de normalização de dados de produtos.

Este módulo fornece funções para normalizar e padronizar dados de produtos,
incluindo nomes, pesos, marcas e códigos EAN.
"""

import re
from typing import Optional, Tuple, Dict
from decimal import Decimal, InvalidOperation


class ProductNormalizer:
    """Serviço para normalização de dados de produtos."""
    
    # Mapa de aliases de marcas conhecidas
    BRAND_ALIASES = {
        'RC': 'Royal Canin',
        'NC': 'Nestlé Purina',
        'PURINA': 'Nestlé Purina',
        'HILLS': "Hill's",
        'PEDIGREE': 'Pedigree',
        'WHISKAS': 'Whiskas',
        'PREMIER': 'Premier Pet',
        'GOLDEN': 'Golden',
        'BIOFRESH': 'Biofresh',
        'FARMINA': 'Farmina',
        'ORIJEN': 'Orijen',
        'ACANA': 'Acana',
    }
    
    # Marcas com capitalização específica
    BRAND_CAPITALIZATION = {
        'royal canin': 'Royal Canin',
        "hill's": "Hill's",
        'nestlé purina': 'Nestlé Purina',
        'premier pet': 'Premier Pet',
        'pro plan': 'Pro Plan',
        'dog chow': 'Dog Chow',
        'cat chow': 'Cat Chow',
        'friskies': 'Friskies',
        'felix': 'Felix',
        'pedigree': 'Pedigree',
        'whiskas': 'Whiskas',
        'golden': 'Golden',
        'biofresh': 'Biofresh',
        'farmina': 'Farmina',
        'orijen': 'Orijen',
        'acana': 'Acana',
    }
    
    # Prefixos redundantes para remover
    REDUNDANT_PREFIXES = [
        'produto:', 'produto -', 'produto',
        'item:', 'item -', 'item',
        'ração:', 'ração -', 'ração',
        'alimento:', 'alimento -', 'alimento',
        'petisco:', 'petisco -', 'petisco',
        'brinquedo:', 'brinquedo -', 'brinquedo',
        'acessório:', 'acessório -', 'acessório',
    ]
    
    # Siglas que devem permanecer em maiúsculo
    PRESERVE_ACRONYMS = [
        'EAN', 'SKU', 'IA', 'AI', 'DNA', 'DHA', 'EPA', 'CBD', 'UV', 'LED',
        'GPS', 'RFID', 'QR', 'USB', 'PET', 'LTDA', 'SA', 'ME', 'EPP'
    ]
    
    @staticmethod
    def normalize_product_name(name: str) -> str:
        """
        Normaliza o nome do produto.
        
        Args:
            name: Nome do produto a ser normalizado
            
        Returns:
            Nome normalizado
            
        Examples:
            >>> normalize_product_name("  PRODUTO: Ração Golden 15 KG  ")
            "Ração Golden 15kg"
            >>> normalize_product_name("item - Petisco para cães")
            "Petisco Para Cães"
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Remove espaços extras e converte para minúsculo
        normalized = re.sub(r'\s+', ' ', name.strip().lower())
        
        # Remove prefixos redundantes
        for prefix in ProductNormalizer.REDUNDANT_PREFIXES:
            pattern = f'^{re.escape(prefix)}\\s*'
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Remove caracteres especiais desnecessários (mantém hífen, parênteses e números)
        normalized = re.sub(r'[^\w\s\-\(\)\.]', '', normalized)
        
        # Padroniza unidades de peso
        normalized = re.sub(r'(\d+(?:[.,]\d+)?)\s*(kg|g|ml|l)\b', 
                          lambda m: f"{m.group(1).replace(',', '.')}{m.group(2).lower()}", 
                          normalized)
        
        # Aplica Title Case inteligente
        words = normalized.split()
        title_words = []
        
        for word in words:
            # Preserva siglas conhecidas
            if word.upper() in ProductNormalizer.PRESERVE_ACRONYMS:
                title_words.append(word.upper())
            # Preserva números com unidades
            elif re.match(r'\d+(?:[.,]\d+)?(?:kg|g|ml|l)$', word):
                title_words.append(word)
            # Aplica title case normal
            else:
                title_words.append(word.capitalize())
        
        return ' '.join(title_words).strip()
    
    @staticmethod
    def normalize_weight(value: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Normaliza valores de peso/volume.
        
        Args:
            value: String contendo peso/volume (ex: "15 Kg", "500ml", "1.5L")
            
        Returns:
            Tupla (valor_numérico, unidade_normalizada) ou (None, None) se inválido
            
        Examples:
            >>> normalize_weight("15 Kg")
            (15.0, "kg")
            >>> normalize_weight("500 ML")
            (500.0, "ml")
            >>> normalize_weight("1,5 litros")
            (1.5, "l")
        """
        if not value or not isinstance(value, str):
            return (None, None)
        
        # Remove espaços extras e normaliza
        normalized = re.sub(r'\s+', ' ', value.strip().lower())
        
        # Padrões para diferentes formatos de peso/volume
        patterns = [
            # Formato: número + espaço + unidade
            r'(\d+(?:[.,]\d+)?)\s*(kg|quilos?|kilos?|k)\b',
            r'(\d+(?:[.,]\d+)?)\s*(g|gramas?)\b',
            r'(\d+(?:[.,]\d+)?)\s*(ml|mililitros?)\b',
            r'(\d+(?:[.,]\d+)?)\s*(l|litros?)\b',
            r'(\d+(?:[.,]\d+)?)\s*(unidades?|un|pcs?|peças?)\b',
            # Formato: número + unidade (sem espaço)
            r'(\d+(?:[.,]\d+)?)(kg|g|ml|l)\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                try:
                    # Converte vírgula para ponto decimal
                    number_str = match.group(1).replace(',', '.')
                    number = float(Decimal(number_str))
                    
                    # Normaliza a unidade
                    unit = match.group(2).lower()
                    if unit in ['kg', 'quilos', 'kilos', 'k']:
                        return (number, 'kg')
                    elif unit in ['g', 'gramas']:
                        return (number, 'g')
                    elif unit in ['ml', 'mililitros']:
                        return (number, 'ml')
                    elif unit in ['l', 'litros']:
                        return (number, 'l')
                    elif unit in ['unidades', 'un', 'pcs', 'peças']:
                        return (number, 'unidade')
                    else:
                        return (number, unit)
                        
                except (ValueError, InvalidOperation):
                    continue
        
        return (None, None)
    
    @staticmethod
    def normalize_brand(brand: str) -> str:
        """
        Normaliza o nome da marca.
        
        Args:
            brand: Nome da marca a ser normalizada
            
        Returns:
            Nome da marca normalizado
            
        Examples:
            >>> normalize_brand("RC")
            "Royal Canin"
            >>> normalize_brand("hill's pet nutrition")
            "Hill's"
        """
        if not brand or not isinstance(brand, str):
            return ""
        
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', brand.strip())
        
        # Verifica aliases primeiro
        brand_upper = normalized.upper()
        if brand_upper in ProductNormalizer.BRAND_ALIASES:
            return ProductNormalizer.BRAND_ALIASES[brand_upper]
        
        # Verifica capitalização específica
        brand_lower = normalized.lower()
        if brand_lower in ProductNormalizer.BRAND_CAPITALIZATION:
            return ProductNormalizer.BRAND_CAPITALIZATION[brand_lower]
        
        # Remove sufixos comuns de empresas
        suffixes_to_remove = [
            'pet nutrition', 'pet food', 'pet care', 'petcare',
            'ltda', 'ltd', 'sa', 'inc', 'corp', 'corporation',
            'indústria', 'industria', 'comercio', 'comércio'
        ]
        
        for suffix in suffixes_to_remove:
            pattern = f'\\s+{re.escape(suffix)}\\s*$'
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        # Aplica title case se não foi encontrada capitalização específica
        return normalized.title().strip()
    
    @staticmethod
    def normalize_ean(ean: str) -> Optional[str]:
        """
        Normaliza e valida código EAN.
        
        Args:
            ean: Código EAN a ser validado
            
        Returns:
            EAN normalizado se válido, None se inválido
            
        Examples:
            >>> normalize_ean("7891000100103")
            "7891000100103"
            >>> normalize_ean("invalid")
            None
        """
        if not ean or not isinstance(ean, str):
            return None
        
        # Remove espaços, hífens e outros caracteres não numéricos
        clean_ean = re.sub(r'[^\d]', '', ean.strip())
        
        # Verifica se tem o tamanho correto (EAN-8 ou EAN-13)
        if len(clean_ean) not in [8, 13]:
            return None
        
        # Valida checksum
        if not ProductNormalizer._validate_ean_checksum(clean_ean):
            return None
        
        return clean_ean
    
    @staticmethod
    def _validate_ean_checksum(ean: str) -> bool:
        """
        Valida o checksum do código EAN.
        
        Args:
            ean: Código EAN limpo (apenas dígitos)
            
        Returns:
            True se o checksum for válido, False caso contrário
        """
        if len(ean) == 13:
            # EAN-13: soma alternada com pesos 1 e 3
            total = sum(int(digit) * (3 if i % 2 else 1) 
                       for i, digit in enumerate(ean[:-1]))
            check_digit = (10 - (total % 10)) % 10
            return check_digit == int(ean[-1])
        
        elif len(ean) == 8:
            # EAN-8: soma alternada com pesos 3 e 1
            total = sum(int(digit) * (1 if i % 2 else 3) 
                       for i, digit in enumerate(ean[:-1]))
            check_digit = (10 - (total % 10)) % 10
            return check_digit == int(ean[-1])
        
        return False


# Funções de conveniência para uso direto
def normalize_product_name(name: str) -> str:
    """Normaliza o nome do produto."""
    return ProductNormalizer.normalize_product_name(name)


def normalize_weight(value: str) -> Tuple[Optional[float], Optional[str]]:
    """Normaliza valores de peso/volume."""
    return ProductNormalizer.normalize_weight(value)


def normalize_brand(brand: str) -> str:
    """Normaliza o nome da marca."""
    return ProductNormalizer.normalize_brand(brand)


def normalize_ean(ean: str) -> Optional[str]:
    """Normaliza e valida código EAN."""
    return ProductNormalizer.normalize_ean(ean)