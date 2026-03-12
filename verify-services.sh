#!/bin/bash

echo "=== VERIFICAÇÃO DE SERVIÇOS ==="
echo "Testando conectividade de todos os serviços..."
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar URL
test_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "Testando $name ($url)... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 30 "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ] || [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
        echo -e "${GREEN}✓ OK ($response)${NC}"
        return 0
    else
        echo -e "${RED}✗ ERRO ($response)${NC}"
        return 1
    fi
}

# Função para testar container Docker
test_container() {
    local container_name=$1
    local service_name=$2
    
    echo -n "Testando container $service_name ($container_name)... "
    
    if docker ps --format "table {{.Names}}" | grep -q "^$container_name$"; then
        echo -e "${GREEN}✓ Rodando${NC}"
        return 0
    else
        echo -e "${RED}✗ Não encontrado${NC}"
        return 1
    fi
}

echo -e "${YELLOW}=== TESTANDO CONTAINERS ===${NC}"
test_container "traefik" "Traefik"
test_container "sixpet-catalog-postgres" "PostgreSQL"
test_container "sixpet-catalog-redis" "Redis"
test_container "sixpet-catalog-api" "API Backend"
test_container "sixpet-catalog-frontend" "Frontend"

echo ""
echo -e "${YELLOW}=== TESTANDO SERVIÇOS PRINCIPAIS ===${NC}"
test_url "https://mins3.sxconnect.com.br" "MinIO"
test_url "https://papi.sxconnect.com.br" "PAPI"
test_url "https://portainer.sxconnect.com.br" "Portainer"

echo ""
echo -e "${YELLOW}=== TESTANDO NOVOS SERVIÇOS DO CATÁLOGO ===${NC}"
test_url "https://sixpetapi.sxconnect.com.br/health" "API Catálogo"
test_url "https://catalog.sxconnect.com.br" "Frontend Catálogo"

echo ""
echo -e "${YELLOW}=== TESTANDO ENDPOINTS DA API ===${NC}"
test_url "https://sixpetapi.sxconnect.com.br/docs" "Swagger Docs"
test_url "https://sixpetapi.sxconnect.com.br/api/health" "Health Check"
test_url "https://sixpetapi.sxconnect.com.br/api/status" "Status API"

echo ""
echo -e "${YELLOW}=== VERIFICANDO LOGS (últimas 5 linhas) ===${NC}"
echo "Logs do Traefik:"
docker logs traefik --tail=5 2>/dev/null || echo "Traefik não encontrado"

echo ""
echo "Logs da API:"
docker logs sixpet-catalog-api --tail=5 2>/dev/null || echo "API não encontrada"

echo ""
echo "Logs do Frontend:"
docker logs sixpet-catalog-frontend --tail=5 2>/dev/null || echo "Frontend não encontrado"

echo ""
echo -e "${YELLOW}=== VERIFICANDO REDES DOCKER ===${NC}"
echo "Redes disponíveis:"
docker network ls | grep -E "(portainer|traefik)"

echo ""
echo -e "${YELLOW}=== RESUMO ===${NC}"
if docker ps | grep -q traefik && docker ps | grep -q sixpet-catalog; then
    echo -e "${GREEN}✓ Sistema aparenta estar funcionando${NC}"
    echo "Acesse: https://catalog.sxconnect.com.br"
else
    echo -e "${RED}✗ Problemas detectados - verificar containers${NC}"
fi

echo ""
echo -e "${YELLOW}Para monitoramento contínuo, execute:${NC}"
echo "watch -n 5 'docker ps | grep -E \"(traefik|sixpet-catalog)\"'"