#!/bin/bash

# Script para deploy do microserviço URL Extractor
# Resolve os conflitos de rotas do FastAPI usando arquitetura de microserviços

set -e

echo "🚀 Iniciando deploy do microserviço URL Extractor..."

# Parar containers existentes
echo "⏹️  Parando containers..."
docker compose down

# Rebuild dos serviços
echo "🔨 Rebuilding containers..."
docker compose build --no-cache

# Iniciar todos os serviços
echo "▶️  Iniciando serviços..."
docker compose up -d

# Aguardar inicialização
echo "⏳ Aguardando inicialização dos serviços..."
sleep 15

# Verificar status dos containers
echo "📊 Status dos containers:"
docker compose ps

# Testar conectividade dos serviços
echo "🔍 Testando conectividade..."

# Testar API principal
echo -n "API Principal (porta 8000): "
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FALHOU"
fi

# Testar microserviço URL Extractor
echo -n "Microserviço URL Extractor (porta 8001): "
if curl -s -f http://localhost:8001/health > /dev/null; then
    echo "✅ OK"
else
    echo "❌ FALHOU"
fi

# Testar endpoints proxy
echo "🔗 Testando endpoints proxy..."

endpoints=(
    "/api/sitemap/health"
    "/api/sitemap/debug"
    "/api/sitemap/products"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "GET $endpoint: "
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint")
    if [ "$status_code" = "200" ]; then
        echo "✅ $status_code"
    else
        echo "❌ $status_code"
    fi
done

# Testar smart-extract (deve retornar 422 sem URL)
echo -n "GET /api/sitemap/smart-extract (sem URL): "
status_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/sitemap/smart-extract")
if [ "$status_code" = "422" ]; then
    echo "✅ $status_code (esperado - parâmetro faltando)"
else
    echo "❌ $status_code (esperado 422)"
fi

echo ""
echo "🎉 Deploy concluído!"
echo ""
echo "📋 Resumo dos serviços:"
echo "   • API Principal: http://localhost:8000"
echo "   • Microserviço URL Extractor: http://localhost:8001"
echo "   • Documentação API: http://localhost:8000/docs"
echo ""
echo "🧪 Para testar extração de URL:"
echo "   curl 'http://localhost:8000/api/sitemap/smart-extract?url=https://www.cobasi.com.br/institucional/categorias'"
echo ""
echo "📊 Para monitorar logs:"
echo "   docker compose logs -f api"
echo "   docker compose logs -f url-extractor"