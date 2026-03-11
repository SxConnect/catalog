#!/bin/bash

# Deploy Script para SixPet Catalog Engine
# Usa imagens do GitHub Container Registry

set -e

echo "🚀 Iniciando deploy do SixPet Catalog Engine..."

# Verificar se o arquivo .env existe
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "📝 Copie o .env.prod.example para .env e configure as variáveis:"
    echo "   cp .env.prod.example .env"
    exit 1
fi

# Parar containers existentes
echo "🛑 Parando containers existentes..."
docker-compose -f docker-compose.prod.yml down

# Fazer pull das imagens mais recentes
echo "📥 Baixando imagens mais recentes do GHCR..."
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Subir os serviços
echo "🔄 Iniciando serviços..."
docker-compose -f docker-compose.prod.yml up -d

# Aguardar o banco de dados estar pronto
echo "⏳ Aguardando banco de dados..."
sleep 10

# Executar migrações
echo "🗄️ Executando migrações do banco de dados..."
docker exec sixpet-catalog-api alembic upgrade head

# Verificar status dos containers
echo "📊 Status dos containers:"
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
echo "📋 Últimos logs do backend:"
docker logs --tail 20 sixpet-catalog-api

echo "📋 Últimos logs do frontend:"
docker logs --tail 20 sixpet-catalog-frontend

echo "✅ Deploy concluído!"
echo ""
echo "🌐 URLs de acesso:"
echo "   Frontend: https://catalog.sxconnect.com.br"
echo "   Backend API: https://catalog-api.sxconnect.com.br"
echo "   Documentação: https://catalog-api.sxconnect.com.br/docs"
echo ""
echo "🔧 Comandos úteis:"
echo "   Ver logs: docker logs -f sixpet-catalog-api"
echo "   Reiniciar: docker restart sixpet-catalog-api"
echo "   Parar tudo: docker-compose -f docker-compose.prod.yml down"