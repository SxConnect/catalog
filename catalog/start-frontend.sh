#!/bin/bash

echo "🎨 Iniciando Frontend em Desenvolvimento"
echo ""

cd frontend

# Verificar se node_modules existe
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependências..."
    npm install
    echo ""
fi

# Verificar se .env.local existe
if [ ! -f .env.local ]; then
    echo "📝 Criando .env.local..."
    cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=admin123
EOF
    echo "✅ .env.local criado"
    echo ""
fi

echo "🚀 Iniciando Next.js..."
echo "   URL: http://localhost:3000"
echo ""
echo "📧 Login:"
echo "   Email: admin@sixpet.com"
echo "   Senha: admin123"
echo ""

npm run dev

