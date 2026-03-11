#!/bin/bash

echo "🚀 Iniciando SixPet Catalog Manager em Desenvolvimento"
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "📝 Criando .env a partir do .env.example..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e adicione suas chaves GROQ_API_KEYS"
    echo ""
fi

# Verificar se frontend/.env.local existe
if [ ! -f frontend/.env.local ]; then
    echo "📝 Criando frontend/.env.local..."
    cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=admin123
EOF
    echo "✅ frontend/.env.local criado"
    echo ""
fi

echo "🐘 Subindo PostgreSQL, Redis e MinIO..."
docker-compose up -d postgres redis minio

echo ""
echo "⏳ Aguardando serviços iniciarem (10 segundos)..."
sleep 10

echo ""
echo "🔄 Rodando migrations..."
docker-compose run --rm api alembic upgrade head

echo ""
echo "🚀 Subindo Backend API..."
echo "   URL: http://localhost:8000"
echo ""
docker-compose up api

