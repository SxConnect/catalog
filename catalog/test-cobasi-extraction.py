#!/usr/bin/env python3
"""
Script para testar extração da Cobasi localmente
"""
import asyncio
import sys
import os

# Adicionar o diretório app ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.tasks.cobasi_worker import CobasiExtractor

async def test_cobasi_extraction():
    """Testa extração da Cobasi"""
    print("🧪 Testando extração da Cobasi...")
    
    extractor = CobasiExtractor()
    
    # Criar tabela
    await extractor.create_cobasi_table()
    print("✅ Tabela criada")
    
    # Testar extração de uma categoria específica
    test_category = "https://www.cobasi.com.br/c/cachorro/racao"
    
    import aiohttp
    async with aiohttp.ClientSession(headers=extractor.headers) as session:
        # Extrair produtos da categoria
        product_urls = await extractor.extract_products_from_category(test_category, session)
        print(f"🛍️ Encontrados {len(product_urls)} produtos na categoria")
        
        # Testar extração de detalhes do primeiro produto
        if product_urls:
            first_product_url = product_urls[0]
            print(f"🔍 Testando extração de: {first_product_url}")
            
            product_data = await extractor.extract_product_details(first_product_url, session)
            
            if product_data:
                print(f"✅ Produto extraído com sucesso:")
                print(f"   Nome: {product_data['name']}")
                print(f"   Marca: {product_data['brand']}")
                print(f"   Preço: R$ {product_data['price']}")
                print(f"   SKU: {product_data['sku']}")
                print(f"   Porte: {product_data['ficha_tecnica'].get('porte', 'N/A')}")
                
                # Salvar no banco
                await extractor.save_product(product_data)
                print(f"💾 Produto salvo no banco de dados")
                
            else:
                print(f"❌ Falha na extração do produto")
        else:
            print(f"❌ Nenhum produto encontrado na categoria")

if __name__ == "__main__":
    asyncio.run(test_cobasi_extraction())