#!/bin/bash

# Script de Release para SixPet Catalog
# Uso: ./release.sh 1.0.6 1.0.2

set -e

BACKEND_VERSION=$1
FRONTEND_VERSION=$2

if [ -z "$BACKEND_VERSION" ] || [ -z "$FRONTEND_VERSION" ]; then
    echo "❌ Uso: ./release.sh <backend_version> <frontend_version>"
    echo "   Exemplo: ./release.sh 1.0.6 1.0.2"
    exit 1
fi

echo "🚀 Iniciando release..."
echo "   Backend: v$BACKEND_VERSION"
echo "   Frontend: v$FRONTEND_VERSION"
echo ""

# Verificar se está no branch main
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Você não está no branch main (atual: $CURRENT_BRANCH)"
    read -p "Continuar mesmo assim? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verificar se há mudanças não commitadas
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Há mudanças não commitadas"
    git status -s
    read -p "Fazer commit agora? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "Mensagem do commit: " COMMIT_MSG
        git commit -m "$COMMIT_MSG"
    else
        exit 1
    fi
fi

# Criar tag do backend
echo "📦 Criando tag do backend: v$BACKEND_VERSION"
git tag -a "v$BACKEND_VERSION" -m "Release v$BACKEND_VERSION - Backend"

# Criar tag do frontend
echo "📦 Criando tag do frontend: v$FRONTEND_VERSION"
git tag -a "frontend-v$FRONTEND_VERSION" -m "Release v$FRONTEND_VERSION - Frontend"

# Push
echo "⬆️  Fazendo push..."
git push origin main
git push origin "v$BACKEND_VERSION"
git push origin "frontend-v$FRONTEND_VERSION"

echo ""
echo "✅ Tags criadas e pushed com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Aguarde GitHub Actions completar builds"
echo "      https://github.com/sxconnect/catalog/actions"
echo ""
echo "   2. Verifique imagens no GHCR:"
echo "      https://github.com/orgs/sxconnect/packages"
echo ""
echo "   3. No servidor, execute:"
echo "      docker-compose -f docker-compose.prod.yml pull"
echo "      docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "   4. Verifique logs:"
echo "      docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "🎉 Release v$BACKEND_VERSION + v$FRONTEND_VERSION iniciado!"
