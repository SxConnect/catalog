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

@router.get("/health")
async def health_check():
    """Health check para o módulo sitemap"""
    return {"status": "ok", "module": "sitemap"}

@router.get("/api")
async def sitemap_api(
    action: str = Query(..., description="Ação: debug, products, smart-extract"),
    url: Optional[str] = Query(None, description="URL para extração (obrigatório para smart-extract)"),
    max_products: int = Query(20, description="Máximo de produtos para extrair"),
    limit: int = Query(10, description="Limite de produtos para listar"),
    db: Session = Depends(get_db)
):
    """
    API consolidada do sitemap - todas as funcionalidades em um endpoint
    
    Ações disponíveis:
    - debug: Informações de debug
    - products: Lista produtos extraídos
    - smart-extract: Extração inteligente de URL (requer parâmetro url)
    """
    try:
        if action == "debug":
            return {
                "status": "debug",
                "message": "Debug endpoint working",
                "available_actions": ["debug", "products", "smart-extract"],
                "endpoints": 2
            }
        
        elif action == "products":
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
                "action": "products",
                "count": len(products),
                "products": products
            }
        
        elif action == "smart-extract":
            if not url:
                raise HTTPException(status_code=422, detail="URL é obrigatório para smart-extract")
            
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
                
                # Extração básica de produto
                product_data = {
                    'source_url': url,
                    'name': None,
                    'brand': None,
                    'price': None,
                    'description': None,
                    'images': []
                }
                
                # Extrair nome
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
                
                # Salvar no banco se encontrou dados
                if product_data['name']:
                    result = db.execute(text("""
                        INSERT INTO url_products (name, brand, description, images, source_url, price)
                        VALUES (:name, :brand, :description, :images, :source_url, :price)
                        RETURNING id
                    """), {
                        'name': product_data['name'],
                        'brand': product_data['brand'] or 'Unknown',
                        'description': product_data['description'] or '',
                        'images': str(product_data['images']),
                        'source_url': url,
                        'price': product_data['price']
                    })
                    
                    product_id = result.scalar()
                    db.commit()
                    
                    return {
                        "status": "success",
                        "action": "smart-extract",
                        "url": url,
                        "product_id": product_id,
                        "product_data": product_data
                    }
                else:
                    return {
                        "status": "success",
                        "action": "smart-extract",
                        "url": url,
                        "message": "Nenhum produto encontrado na URL"
                    }
        
        else:
            raise HTTPException(status_code=400, detail=f"Ação '{action}' não reconhecida. Use: debug, products, smart-extract")
    
    except Exception as e:
        logger.error(f"Error in sitemap API action '{action}': {e}")
        raise HTTPException(status_code=500, detail=f"Erro na ação '{action}': {str(e)}")

@router.post("/test-scrape")
async def test_scrape(url: str = Query(...)):
    """Teste de scraping - funcionalidade separada"""
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
            
            return {
                "status": "success",
                "product_data": product_data
            }
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping error: {str(e)}")