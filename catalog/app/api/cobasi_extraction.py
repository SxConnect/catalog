"""
API endpoints para controlar extração da Cobasi
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from app.logger import logger
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.tasks.cobasi_worker import extract_cobasi_products
import asyncio
import asyncpg
from app.config import settings
from typing import Optional

router = APIRouter()

@router.post("/start-extraction")
async def start_cobasi_extraction():
    """Inicia extração em massa da Cobasi"""
    try:
        # Iniciar tarefa assíncrona
        task = extract_cobasi_products.delay()
        
        logger.info(f"🚀 Extração da Cobasi iniciada - Task ID: {task.id}")
        
        return {
            "status": "success",
            "message": "Extração da Cobasi iniciada com sucesso",
            "task_id": task.id,
            "info": "A extração roda em background e não interfere no processamento de PDFs"
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar extração da Cobasi: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar extração: {str(e)}")

@router.get("/status")
async def get_extraction_status():
    """Verifica status da extração da Cobasi"""
    try:
        # Conectar ao banco para verificar estatísticas
        conn = await asyncpg.connect(settings.database_url)
        
        try:
            # Verificar se tabela existe
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'unified_products'
                )
            """)
            
            if not table_exists:
                return {
                    "status": "not_started",
                    "message": "Extração ainda não foi iniciada",
                    "products_count": 0
                }
            
            # Contar produtos extraídos da Cobasi
            total_products = await conn.fetchval("""
                SELECT COUNT(*) FROM unified_products 
                WHERE source_type = 'cobasi'
            """)
            
            # Produtos extraídos hoje
            today_products = await conn.fetchval("""
                SELECT COUNT(*) FROM unified_products 
                WHERE source_type = 'cobasi' 
                AND DATE(created_at) = CURRENT_DATE
            """)
            
            # Últimos produtos extraídos
            recent_products = await conn.fetch("""
                SELECT sku, name, brand, price, created_at
                FROM unified_products 
                WHERE source_type = 'cobasi'
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            recent_list = []
            for product in recent_products:
                recent_list.append({
                    "sku": product['sku'],
                    "name": product['name'][:50] + "..." if product['name'] and len(product['name']) > 50 else product['name'],
                    "brand": product['brand'],
                    "price": float(product['price']) if product['price'] else None,
                    "extracted_at": product['created_at'].isoformat()
                })
            
            return {
                "status": "running" if today_products > 0 else "completed",
                "total_products": total_products,
                "products_today": today_products,
                "recent_products": recent_list,
                "message": f"Total de {total_products} produtos da Cobasi no banco"
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar status: {str(e)}")

@router.get("/products")
async def list_cobasi_products(
    limit: int = Query(20, description="Número máximo de produtos"),
    brand: Optional[str] = Query(None, description="Filtrar por marca"),
    search: Optional[str] = Query(None, description="Buscar no nome do produto")
):
    """Lista produtos extraídos da Cobasi"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        
        try:
            # Construir query com filtros
            where_conditions = ["source_type = 'cobasi'"]
            params = []
            param_count = 0
            
            if brand:
                param_count += 1
                where_conditions.append(f"brand ILIKE ${param_count}")
                params.append(f"%{brand}%")
            
            if search:
                param_count += 1
                where_conditions.append(f"name ILIKE ${param_count}")
                params.append(f"%{search}%")
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            param_count += 1
            query = f"""
                SELECT sku, name, brand, price, source_url, porte, tipo_produto, 
                       peso_produto, sabor, created_at
                FROM unified_products 
                {where_clause}
                ORDER BY created_at DESC 
                LIMIT ${param_count}
            """
            params.append(limit)
            
            products = await conn.fetch(query, *params)
            
            product_list = []
            for product in products:
                product_list.append({
                    "sku": product['sku'],
                    "name": product['name'],
                    "brand": product['brand'],
                    "price": float(product['price']) if product['price'] else None,
                    "url": product['source_url'],
                    "porte": product['porte'],
                    "tipo_produto": product['tipo_produto'],
                    "peso_produto": product['peso_produto'],
                    "sabor": product['sabor'],
                    "extracted_at": product['created_at'].isoformat() if product['created_at'] else None
                })
            
            return {
                "status": "success",
                "count": len(product_list),
                "products": product_list,
                "filters": {
                    "brand": brand,
                    "search": search,
                    "limit": limit
                }
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao listar produtos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar produtos: {str(e)}")

@router.get("/stats")
async def get_extraction_stats():
    """Estatísticas detalhadas da extração"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        
        try:
            # Verificar se tabela existe
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'unified_products'
                )
            """)
            
            if not table_exists:
                return {
                    "status": "not_started",
                    "message": "Extração ainda não foi iniciada"
                }
            
            # Estatísticas gerais da Cobasi
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(DISTINCT brand) as total_brands,
                    AVG(price) as avg_price,
                    MIN(price) as min_price,
                    MAX(price) as max_price,
                    MIN(created_at) as first_extraction,
                    MAX(created_at) as last_extraction
                FROM unified_products
                WHERE source_type = 'cobasi' AND price IS NOT NULL
            """)
            
            # Top marcas
            top_brands = await conn.fetch("""
                SELECT brand, COUNT(*) as product_count
                FROM unified_products 
                WHERE source_type = 'cobasi' AND brand IS NOT NULL
                GROUP BY brand 
                ORDER BY product_count DESC 
                LIMIT 10
            """)
            
            # Produtos por tipo
            tipos_produto = await conn.fetch("""
                SELECT tipo_produto, COUNT(*) as count
                FROM unified_products 
                WHERE source_type = 'cobasi' AND tipo_produto IS NOT NULL
                GROUP BY tipo_produto 
                ORDER BY count DESC
            """)
            
            return {
                "status": "success",
                "general_stats": {
                    "total_products": stats['total_products'],
                    "total_brands": stats['total_brands'],
                    "avg_price": float(stats['avg_price']) if stats['avg_price'] else None,
                    "min_price": float(stats['min_price']) if stats['min_price'] else None,
                    "max_price": float(stats['max_price']) if stats['max_price'] else None,
                    "first_extraction": stats['first_extraction'].isoformat() if stats['first_extraction'] else None,
                    "last_extraction": stats['last_extraction'].isoformat() if stats['last_extraction'] else None
                },
                "top_brands": [{"brand": row['brand'], "count": row['product_count']} for row in top_brands],
                "tipos_produto": [{"tipo": row['tipo_produto'], "count": row['count']} for row in tipos_produto]
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@router.delete("/reset")
async def reset_cobasi_data():
    """Remove todos os dados da Cobasi (usar com cuidado!)"""
    try:
        conn = await asyncpg.connect(settings.database_url)
        
        try:
            # Contar produtos antes de deletar
            count_before = await conn.fetchval("""
                SELECT COUNT(*) FROM unified_products 
                WHERE source_type = 'cobasi'
            """)
            
            # Deletar todos os produtos da Cobasi
            await conn.execute("DELETE FROM unified_products WHERE source_type = 'cobasi'")
            
            logger.warning(f"🗑️ Removidos {count_before} produtos da Cobasi do banco")
            
            return {
                "status": "success",
                "message": f"Removidos {count_before} produtos da Cobasi",
                "products_removed": count_before
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao resetar dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao resetar dados: {str(e)}")