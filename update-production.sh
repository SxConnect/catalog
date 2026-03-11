#!/bin/bash

# Script de Atualização para VPS - SixPet Catalog Engine
# Atualiza as imagens do GHCR e reinicia os serviços

set -e

echo "🔄 Atualizando SixPet Catalog Engine na VPS..."

# Verificar se estamos no diretório correto
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Arquivo docker-compose.prod.yml não encontrado!"
    echo "📁 Execute este script no diretório do projeto"
    exit 1
fi

# Fazer backup do estado atual
echo "💾 Fazendo backup do estado atual..."
docker-compose -f docker-compose.prod.yml ps > backup-status-$(date +%Y%m%d-%H%M%S).txt

# Parar os serviços (mantendo banco e redis rodando)
echo "🛑 Parando serviços da aplicação..."
docker-compose -f docker-compose.prod.yml stop api worker frontend

# Fazer pull das imagens mais recentes
echo "📥 Baixando imagens mais recentes do GHCR..."
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Remover containers antigos
echo "🗑️ Removendo containers antigos..."
docker-compose -f docker-compose.prod.yml rm -f api worker frontend

# Subir os serviços atualizados
echo "🚀 Iniciando serviços atualizados..."
docker-compose -f docker-compose.prod.yml up -d api worker frontend

# Aguardar os serviços estarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 15

# Executar migrações se necessário
echo "🗄️ Verificando migrações do banco de dados..."
docker exec sixpet-catalog-api alembic upgrade head

# Verificar status dos serviços
echo "📊 Status dos serviços atualizados:"
docker-compose -f docker-compose.prod.yml ps

# Verificar saúde dos serviços
echo "🏥 Verificando saúde dos serviços..."
echo "Backend API:"
curl -f https://catalog-api.sxconnect.com.br/health || echo "⚠️ Backend não respondeu"

echo "Frontend:"
curl -f https://catalog.sxconnect.com.br/api/health || echo "⚠️ Frontend não respondeu"

# Mostrar logs recentes
echo "📋 Logs recentes do backend:"
docker logs --tail 10 sixpet-catalog-api

echo "📋 Logs recentes do frontend:"
docker logs --tail 10 sixpet-catalog-frontend

echo "✅ Atualização concluída!"
echo ""
echo "🌐 URLs de acesso:"
echo "   Frontend: https://catalog.sxconnect.com.br"
echo "   Backend API: https://catalog-api.sxconnect.com.br"
echo "   Documentação: https://catalog-api.sxconnect.com.br/docs"
echo ""
echo "🔧 Comandos úteis:"
echo "   Ver logs: docker logs -f sixpet-catalog-api"
echo "   Reiniciar: docker restart sixpet-catalog-api"
echo "   Status: docker-compose -f docker-compose.prod.yml ps"