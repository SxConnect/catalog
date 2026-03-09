#!/bin/bash

echo "🔍 Verificando se imagens v1.0.0 estão disponíveis no GHCR..."
echo ""

# Verificar backend
echo "📦 Backend (catalog:1.0.0):"
if docker pull ghcr.io/sxconnect/catalog:1.0.0 2>/dev/null; then
    echo "✅ Imagem disponível!"
else
    echo "❌ Imagem ainda não disponível. Aguarde o build completar."
fi

echo ""

# Verificar frontend
echo "📦 Frontend (catalog-frontend:1.0.0):"
if docker pull ghcr.io/sxconnect/catalog-frontend:1.0.0 2>/dev/null; then
    echo "✅ Imagem disponível!"
else
    echo "❌ Imagem ainda não disponível. Aguarde o build completar."
fi

echo ""
echo "📊 Status dos builds: https://github.com/SxConnect/catalog/actions"
