#!/bin/bash

# Script para executar migrações pendentes no banco de dados
# Deve ser executado no container da API

echo "🔄 Executando migrações pendentes..."

# Executar migrações do Alembic
alembic upgrade head

echo "✅ Migrações executadas com sucesso!"

# Verificar se as colunas foram criadas
echo "🔍 Verificando estrutura da tabela products_catalog..."
python -c "
from app.database import engine
import sqlalchemy as sa

with engine.connect() as conn:
    result = conn.execute(sa.text(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'products_catalog' AND column_name IN ('ingredients', 'nutritional_info')\"))
    columns = [row[0] for row in result]
    
    if 'ingredients' in columns and 'nutritional_info' in columns:
        print('✅ Colunas ingredients e nutritional_info encontradas!')
    else:
        print('❌ Colunas não encontradas. Migrações podem não ter sido aplicadas.')
        print(f'Colunas encontradas: {columns}')
"

echo "🎯 Script concluído!"