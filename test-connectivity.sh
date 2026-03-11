#!/bin/bash

# Script para testar conectividade entre frontend e backend

echo "🔍 Testando conectividade Frontend <-> Backend..."
echo "================================================"

# Testar backend diretamente
echo "🔧 Testando Backend API:"
echo "URL: https://catalog-api.sxconnect.com.br/health"
if curl -f -s https://catalog-api.sxconnect.com.br/health > /dev/null; then
    echo "✅ Backend API respondendo"
    curl -s https://catalog-api.sxconnect.com.br/health | jq . 2>/dev/null || curl -s https://catalog-api.sxconnect.com.br/health
else
    echo "❌ Backend API não responde"
fi

echo ""

# Testar frontend
echo "🌐 Testando Frontend:"
echo "URL: https://catalog.sxconnect.com.br/api/health"
if curl -f -s https://catalog.sxconnect.com.br/api/health > /dev/null; then
    echo "✅ Frontend respondendo"
    curl -s https://catalog.sxconnect.com.br/api/health | jq . 2>/dev/null || curl -s https://catalog.sxconnect.com.br/api/health
else
    echo "❌ Frontend não responde"
fi

echo ""

# Testar endpoint de debug
echo "🐛 Testando configuração do Frontend:"
echo "URL: https://catalog.sxconnect.com.br/api/debug"
if curl -f -s https://catalog.sxconnect.com.br/api/debug > /dev/null; then
    echo "✅ Debug endpoint respondendo"
    curl -s https://catalog.sxconnect.com.br/api/debug | jq . 2>/dev/null || curl -s https://catalog.sxconnect.com.br/api/debug
else
    echo "❌ Debug endpoint não responde (normal se ainda não foi deployado)"
fi

echo ""

# Testar conectividade interna dos containers
echo "🐳 Testando conectividade interna dos containers:"
echo "Frontend -> Backend (interno):"
if docker exec sixpet-catalog-frontend curl -f -s http://api:8000/health > /dev/null 2>&1; then
    echo "✅ Conectividade interna OK"
else
    echo "❌ Problema na conectividade interna"
fi

echo ""

# Verificar variáveis de ambiente
echo "🔧 Verificando variáveis de ambiente do Frontend:"
docker exec sixpet-catalog-frontend env | grep -E "(NEXT_PUBLIC_|API_)" || echo "❌ Variáveis não encontradas"

echo ""
echo "📊 Logs recentes do Frontend:"
docker logs --tail 10 sixpet-catalog-frontend

echo ""
echo "✅ Teste de conectividade concluído!"