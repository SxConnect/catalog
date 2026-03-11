#!/bin/bash

echo "=== CORREÇÃO DO BANCO DE DADOS SIXPET CATALOG ==="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Passo 1: Verificando containers...${NC}"
docker ps | grep sixpet-catalog

echo ""
echo -e "${YELLOW}Passo 2: Conectando ao PostgreSQL e corrigindo ENUM...${NC}"
docker exec -i sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog << 'EOF'
-- Verificar status atual
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'catalogs' AND column_name = 'status';

-- Corrigir ENUM
ALTER TABLE catalogs ALTER COLUMN status TYPE text;
DROP TYPE IF EXISTS catalogstatus CASCADE;
CREATE TYPE catalogstatus AS ENUM ('uploaded', 'processing', 'completed', 'failed');
UPDATE catalogs SET status = LOWER(status) WHERE status IS NOT NULL;
ALTER TABLE catalogs ALTER COLUMN status TYPE catalogstatus USING status::catalogstatus;
ALTER TABLE catalogs ALTER COLUMN status SET DEFAULT 'uploaded';

-- Verificar correção
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'catalogs' AND column_name = 'status';

-- Mostrar dados atuais
SELECT id, filename, status, created_at FROM catalogs ORDER BY id DESC LIMIT 5;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ENUM corrigido com sucesso!${NC}"
else
    echo -e "${RED}✗ Erro ao corrigir ENUM${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Passo 3: Testando conexão da API...${NC}"
docker exec sixpet-catalog-api curl -s http://localhost:8000/health

echo ""
echo -e "${YELLOW}Passo 4: Verificando logs da API...${NC}"
docker logs sixpet-catalog-api --tail 20

echo ""
echo -e "${GREEN}=== CORREÇÃO CONCLUÍDA ===${NC}"
echo ""
echo "Próximos passos:"
echo "1. Acesse: https://catalog.sxconnect.com.br"
echo "2. Faça login"
echo "3. Vá em 'Upload de Catálogo'"
echo "4. Teste o upload de um PDF"
echo ""
