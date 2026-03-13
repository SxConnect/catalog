#!/bin/bash

echo "Atualizando containers na VPS..."

# Navegar para o diretório do projeto
cd /root/catalog

# Fazer pull da nova imagem
echo "Fazendo pull da nova imagem..."
docker-compose pull api

# Parar containers
echo "Parando containers..."
docker-compose down

# Iniciar containers com nova imagem
echo "Iniciando containers com nova imagem..."
docker-compose up -d

# Aguardar containers iniciarem
echo "Aguardando containers iniciarem..."
sleep 15

# Verificar status
echo "Verificando status dos containers..."
docker-compose ps

# Testar endpoints
echo ""
echo "Testando endpoint de health..."
curl -s http://localhost:8000/api/sitemap/health | jq .

echo ""
echo "Testando extração inteligente..."
curl -s "http://localhost:8000/api/sitemap/smart-extract?url=https://www.bbbpet.com.br/produto/kit-higienico-1-und" | jq .

echo ""
echo "Listando produtos extraídos..."
curl -s "http://localhost:8000/api/sitemap/products" | jq .

echo ""
echo "Atualização concluída!"