"""
Sistema de Crawling e Extração Inteligente de Produtos para o SixPet Catalog Engine.

Este módulo implementa crawling avançado de sites de produtos pet com:
- Navegação automática por links de produtos
- Extração inteligente de dados de produto
- Verificação de duplicatas por título, EAN e marca
- Integração com parsing nutricional
"""

import asyncio
import re
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models import Product
from app.servi