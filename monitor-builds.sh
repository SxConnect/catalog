#!/bin/bash

# Script para monitorar builds do GitHub Actions

echo "🔍 Monitorando builds do GitHub Actions..."
echo "=========================================="

# URLs dos workflows
BACKEND_WORKFLOW="https://github.com/SxConnect/catalog/actions/workflows/docker-publish.yml"
FRONTEND_WORKFLOW="https://github.com/SxConnect/catalog/actions/workflows/docker-publish-frontend.yml"

echo "🔗 Links dos workflows:"
echo "   Backend:  $BACKEND_WORKFLOW"
echo "   Frontend: $FRONTEND_WORKFLOW"
echo ""

# Verificar se as imagens estão disponíveis no GHCR
echo "🐳 Verificando imagens no GHCR..."

echo "Backend:"
if docker pull ghcr.io/sxconnect/catalog-backend:latest > /dev/null 2>&1; then
    echo "✅ ghcr.io/sxconnect/catalog-backend:latest - Disponível"
else
    echo "⏳ ghcr.io/sxconnect/catalog-backend:latest - Aguardando build..."
fi

echo "Frontend:"
if docker pull ghcr.io/sxconnect/catalog-frontend:latest > /dev/null 2>&1; then
    echo "✅ ghcr.io/sxconnect/catalog-frontend:latest - Disponível"
else
    echo "⏳ ghcr.io/sxconnect/catalog-frontend:latest - Aguardando build..."
fi

echo ""
echo "📊 Para acompanhar o progresso:"
echo "   1. Acesse: https://github.com/SxConnect/catalog/actions"
echo "   2. Aguarde os builds completarem (ícones verdes)"
echo "   3. Execute: ./update-production.sh na VPS"
echo ""
echo "🔄 Para verificar novamente, execute: ./monitor-builds.sh"