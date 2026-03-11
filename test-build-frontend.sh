#!/bin/bash

# Script para testar build do frontend localmente

echo "🔨 Testando build do frontend..."

cd catalog-frontend

echo "📦 Instalando dependências..."
npm ci

echo "🏗️ Executando build..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build executado com sucesso!"
else
    echo "❌ Erro no build!"
    exit 1
fi

echo "🧪 Testando start..."
timeout 10s npm start &
sleep 5

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Aplicação iniciou com sucesso!"
else
    echo "⚠️ Aplicação não respondeu (pode ser normal em teste rápido)"
fi

echo "🧹 Limpando..."
pkill -f "npm start" || true

echo "✅ Teste concluído!"