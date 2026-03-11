#!/bin/bash

# Script de verificação do deployment do SixPet Catalog
# Uso: bash check-deployment.sh

echo "🔍 Verificando deployment do SixPet Catalog..."
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# 1. Verificar containers
echo "📦 Verificando containers..."
docker ps --filter "name=sixpet-catalog" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -v "NAMES"
echo ""

# 2. Verificar saúde dos containers
echo "🏥 Verificando saúde dos containers..."
for container in sixpet-catalog-postgres sixpet-catalog-redis sixpet-catalog-api sixpet-catalog-frontend; do
    health=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null)
    if [ "$health" == "healthy" ]; then
        echo -e "${GREEN}✓${NC} $container: healthy"
    elif [ "$health" == "unhealthy" ]; then
        echo -e "${RED}✗${NC} $container: unhealthy"
    else
        status=$(docker inspect --format='{{.State.Status}}' $container 2>/dev/null)
        if [ "$status" == "running" ]; then
            echo -e "${YELLOW}⚠${NC} $container: running (sem healthcheck)"
        else
            echo -e "${RED}✗${NC} $container: $status"
        fi
    fi
done
echo ""

# 3. Verificar PostgreSQL
echo "🗄️  Verificando PostgreSQL..."
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT 1;" > /dev/null 2>&1
check "Conexão com PostgreSQL"

docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "\dt" 2>/dev/null | grep -q "products_catalog"
check "Tabelas criadas"
echo ""

# 4. Verificar Redis
echo "📮 Verificando Redis..."
docker exec sixpet-catalog-redis redis-cli ping > /dev/null 2>&1
check "Conexão com Redis"
echo ""

# 5. Verificar migrations
echo "🔄 Verificando migrations..."
migration=$(docker exec sixpet-catalog-api alembic current 2>/dev/null | grep -o "[0-9a-f]\{12\}")
if [ ! -z "$migration" ]; then
    echo -e "${GREEN}✓${NC} Migration atual: $migration"
else
    echo -e "${RED}✗${NC} Nenhuma migration aplicada"
fi
echo ""

# 6. Verificar endpoints
echo "🌐 Verificando endpoints..."

# Backend health
backend_health=$(curl -s -o /dev/null -w "%{http_code}" https://catalog-api.sxconnect.com.br/health 2>/dev/null)
if [ "$backend_health" == "200" ]; then
    echo -e "${GREEN}✓${NC} Backend API: https://catalog-api.sxconnect.com.br/health (200)"
else
    echo -e "${RED}✗${NC} Backend API: https://catalog-api.sxconnect.com.br/health ($backend_health)"
fi

# Frontend health
frontend_health=$(curl -s -o /dev/null -w "%{http_code}" https://catalog.sxconnect.com.br/api/health 2>/dev/null)
if [ "$frontend_health" == "200" ]; then
    echo -e "${GREEN}✓${NC} Frontend: https://catalog.sxconnect.com.br/api/health (200)"
else
    echo -e "${RED}✗${NC} Frontend: https://catalog.sxconnect.com.br/api/health ($frontend_health)"
fi
echo ""

# 7. Verificar variáveis de ambiente
echo "⚙️  Verificando variáveis de ambiente..."
docker exec sixpet-catalog-api env | grep -q "DATABASE_URL"
check "DATABASE_URL configurada (API)"

docker exec sixpet-catalog-frontend env | grep -q "NEXTAUTH_SECRET"
check "NEXTAUTH_SECRET configurada (Frontend)"

docker exec sixpet-catalog-frontend env | grep -q "ADMIN_EMAIL"
check "ADMIN_EMAIL configurada (Frontend)"
echo ""

# 8. Verificar logs recentes
echo "📋 Últimas linhas dos logs..."
echo ""
echo "--- API ---"
docker logs sixpet-catalog-api --tail 3 2>&1
echo ""
echo "--- Frontend ---"
docker logs sixpet-catalog-frontend --tail 3 2>&1
echo ""
echo "--- Worker ---"
docker logs sixpet-catalog-worker --tail 3 2>&1
echo ""

# Resumo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "URLs:"
echo "  Frontend: https://catalog.sxconnect.com.br"
echo "  Backend:  https://catalog-api.sxconnect.com.br"
echo "  Docs:     https://catalog-api.sxconnect.com.br/docs"
echo ""
echo "Comandos úteis:"
echo "  Ver logs:      docker logs -f sixpet-catalog-[api|frontend|worker]"
echo "  Reiniciar:     docker restart sixpet-catalog-[api|frontend|worker]"
echo "  Migrations:    docker exec sixpet-catalog-api alembic upgrade head"
echo "  PostgreSQL:    docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog"
echo ""
