Write-Host "🎨 Iniciando Frontend em Desenvolvimento" -ForegroundColor Green
Write-Host ""

Set-Location frontend

# Verificar se node_modules existe
if (-not (Test-Path node_modules)) {
    Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

# Verificar se .env.local existe
if (-not (Test-Path .env.local)) {
    Write-Host "📝 Criando .env.local..." -ForegroundColor Yellow
    @"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=admin123
"@ | Out-File -FilePath .env.local -Encoding utf8
    Write-Host "✅ .env.local criado" -ForegroundColor Green
    Write-Host ""
}

Write-Host "🚀 Iniciando Next.js..." -ForegroundColor Green
Write-Host "   URL: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📧 Login:" -ForegroundColor Yellow
Write-Host "   Email: admin@sixpet.com" -ForegroundColor White
Write-Host "   Senha: admin123" -ForegroundColor White
Write-Host ""

npm run dev
