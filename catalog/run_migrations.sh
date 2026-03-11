#!/bin/bash

echo "=== RODANDO MIGRATIONS DO BANCO DE DADOS ==="
echo ""

# Exportar variáveis de ambiente necessárias
export DATABASE_URL="postgresql://sixpet:sixpet123@postgres:5432/sixpet_catalog"

# Rodar migrations
docker exec -e DATABASE_URL="$DATABASE_URL" sixpet-catalog-api alembic upgrade head

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Migrations executadas com sucesso!"
    echo ""
    echo "Verificando tabelas criadas:"
    docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "\dt"
else
    echo ""
    echo "✗ Erro ao executar migrations"
    exit 1
fi
