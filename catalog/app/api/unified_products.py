"""
API endpoints para produtos unificados
Consulta produtos de todas as fontes (Cobasi, catálogos, web)
"""
from fastapi import APIRouter, HTTPException, Query
from app.logger import logger
import asyncpg
from app.config import DATABASE_URL
from typing import Optional

router = APIRouter()

@router.get("/status")
async def get_unified_products_status():
    """Status geral do sistema de produtos unificados"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
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
                    "status": "not_initialized",
                    "message": "Sistema de produtos unificados não foi inicializado"
                }
            
            # Estatísticas por fonte
            stats_by_source = await conn.fetch("""
                SELECT 
                    source_type,
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN is_enriched = true THEN 1 END) as enriched_products,
                    COUNT(DISTINCT brand) as unique_brands,
                    AVG(price) as avg_price
                FROM unified_products 
                GROUP BY source_type
                ORDER BY total_products DESC
            """)
            
            # Total geral
            total_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN is_enriched = true THEN 1 END) as total_enriched,
                    COUNT(DISTINCT brand) as total_brands,
                    COUNT(DISTINCT name_normalized) as unique_products
                FROM unified_products
            """)
            
            # Produtos adicionados hoje
            today_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as products_today,
                    COUNT(CASE WHEN source_type = 'cobasi' THEN 1 END) as cobasi_today,
                    COUNT(CASE WHEN source_type = 'catalog' THEN 1 END) as catalog_today
                FROM unified_products 
                WHERE DATE(created_at) = CURRENT_DATE
            """)
            
            # Últimos produtos adicionados
            recent_products = await conn.fetch("""
                SELECT name, brand, source_type, created_at
                FROM unified_products 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            source_breakdown = []
            for stat in stats_by_source:
                source_breakdown.append({
                    "source": stat['source_type'],
                    "total_products": stat['total_products'],
                    "enriched_products": stat['enriched_products'],
                    "unique_brands": stat['unique_brands'],
                    "avg_price": float(stat['avg_price']) if stat['avg_price'] else None
                })
            
            recent_list = []
            for product in recent_products:
                recent_list.append({
                    "name": product['name'][:50] + "..." if len(product['name']) > 50 else product['name'],
                    "brand": product['brand'],
                    "source": product['source_type'],
                    "added_at": product['created_at'].isoformat()
                })
            
            return {
                "status": "active",
                "total_stats": {
                    "total_products": total_stats['total_products'],
                    "enriched_products": total_stats['total_enriched'],
                    "unique_brands": total_stats['total_brands'],
                    "unique_products": total_stats['unique_products']
                },
                "today_stats": {
                    "products_added_today": today_stats['products_today'],
                    "cobasi_today": today_stats['cobasi_today'],
                    "catalog_today": today_stats['catalog_today']
                },
                "source_breakdown": source_breakdown,
                "recent_products": recent_list
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao obter status dos produtos unificados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@router.get("/search")
async def search_unified_products(
    query: str = Query(..., description="Termo de busca"),
    source: Optional[str] = Query(None, description="Filtrar por fonte (cobasi, catalog, web_enriched)"),
    brand: Optional[str] = Query(None, description="Filtrar por marca"),
    limit: int = Query(20, description="Número máximo de resultados")
):
    """Busca produtos em todas as fontes"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            # Construir query com filtros
            where_conditions = ["(name ILIKE $1 OR brand ILIKE $1 OR name_normalized ILIKE $1)"]
            params = [f"%{query}%"]
            param_count = 1
            
            if source:
                param_count += 1
                where_conditions.append(f"source_type = ${param_count}")
                params.append(source)
            
            if brand:
                param_count += 1
                where_conditions.append(f"brand ILIKE ${param_count}")
                params.append(f"%{brand}%")
            
            where_clause = "WHERE " + " AND ".join(where_conditions)
            
            param_count += 1
            search_query = f"""
                SELECT 
                    id, sku, name, brand, price, source_type, source_url,
                    porte, tipo_produto, peso_produto, sabor, is_enriched,
                    created_at
                FROM unified_products 
                {where_clause}
                ORDER BY 
                    CASE WHEN name ILIKE $1 THEN 1 ELSE 2 END,
                    created_at DESC
                LIMIT ${param_count}
            """
            params.append(limit)
            
            products = await conn.fetch(search_query, *params)
            
            product_list = []
            for product in products:
                product_list.append({
                    "id": product['id'],
                    "sku": product['sku'],
                    "name": product['name'],
                    "brand": product['brand'],
                    "price": float(product['price']) if product['price'] else None,
                    "source": product['source_type'],
                    "url": product['source_url'],
                    "porte": product['porte'],
                    "tipo_produto": product['tipo_produto'],
                    "peso_produto": product['peso_produto'],
                    "sabor": product['sabor'],
                    "is_enriched": product['is_enriched'],
                    "created_at": product['created_at'].isoformat() if product['created_at'] else None
                })
            
            return {
                "status": "success",
                "query": query,
                "filters": {
                    "source": source,
                    "brand": brand,
                    "limit": limit
                },
                "count": len(product_list),
                "products": product_list
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro na busca de produtos unificados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")

@router.get("/duplicates")
async def find_potential_duplicates(
    threshold: float = Query(0.85, description="Threshold de similaridade (0.0 a 1.0)"),
    limit: int = Query(50, description="Número máximo de grupos de duplicatas")
):
    """Encontra possíveis duplicatas no banco"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            # Buscar produtos com nomes similares
            duplicates_query = """
                SELECT 
                    p1.id as id1, p1.name as name1, p1.brand as brand1, p1.source_type as source1,
                    p2.id as id2, p2.name as name2, p2.brand as brand2, p2.source_type as source2,
                    similarity(p1.name_normalized, p2.name_normalized) as similarity_score
                FROM unified_products p1
                JOIN unified_products p2 ON p1.id < p2.id
                WHERE similarity(p1.name_normalized, p2.name_normalized) >= $1
                ORDER BY similarity_score DESC
                LIMIT $2
            """
            
            duplicates = await conn.fetch(duplicates_query, threshold, limit)
            
            duplicate_groups = []
            for dup in duplicates:
                duplicate_groups.append({
                    "similarity_score": float(dup['similarity_score']),
                    "product1": {
                        "id": dup['id1'],
                        "name": dup['name1'],
                        "brand": dup['brand1'],
                        "source": dup['source1']
                    },
                    "product2": {
                        "id": dup['id2'],
                        "name": dup['name2'],
                        "brand": dup['brand2'],
                        "source": dup['source2']
                    }
                })
            
            return {
                "status": "success",
                "threshold": threshold,
                "count": len(duplicate_groups),
                "potential_duplicates": duplicate_groups
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar duplicatas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar duplicatas: {str(e)}")