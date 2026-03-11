#!/bin/bash

# Script de Emergência para Corrigir Problemas de Rede

echo "🚨 Aplicando correção de emergência para problemas de rede..."
echo "============================================================="

# 1. Parar containers problemáticos
echo "🛑 Parando containers frontend e backend..."
docker-compose -f docker-compose.prod.yml stop frontend api worker

# 2. Remover containers para forçar recriação
echo "🗑️ Removendo containers para recriação..."
docker-compose -f docker-compose.prod.yml rm -f frontend api worker

# 3. Limpar cache de rede do Docker
echo "🧹 Limpando cache de rede..."
docker network prune -f

# 4. Baixar imagens mais recentes
echo "📥 Baixando imagens mais recentes..."
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# 5. Recriar containers com configuração de rede corrigida
echo "🔄 Recriando containers..."
docker-compose -f docker-compose.prod.yml up -d api worker frontend

# 6. Aguardar containers ficarem prontos
echo "⏳ Aguardando containers ficarem prontos..."
sleep 20

# 7. Executar migrações
echo "🗄️ Executando migrações..."
docker exec sixpet-catalog-api alembic upgrade head

# 8. Testar conectividade
echo "🔍 Testando conectividade..."

echo "Backend API:"
if curl -f -s https://catalog-api.sxconnect.com.br/health > /dev/null; then
    echo "✅ Backend OK"
else
    echo "❌ Backend com problemas"
fi

echo "Frontend:"
if curl -f -s https://catalog.sxconnect.com.br/api/health > /dev/null; then
    echo "✅ Frontend OK"
else
    echo "❌ Frontend com problemas"
fi

# 9. Verificar logs
echo "📋 Logs recentes do Frontend:"
docker logs --tail 10 sixpet-catalog-frontend

echo "📋 Logs recentes do Backend:"
docker logs --tail 10 sixpet-catalog-api

# 10. Status final
echo "📊 Status dos containers:"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo "✅ Correção de emergência aplicada!"
echo ""
echo "🌐 Teste agora:"
echo "   Frontend: https://catalog.sxconnect.com.br"
echo "   Backend: https://catalog-api.sxconnect.com.br/health"
echo ""
echo "Se ainda houver problemas, execute:"
echo "   docker logs -f sixpet-catalog-frontend"
echo "   docker logs -f sixpet-catalog-api"