Write-Host "🚀 Iniciando SixPet Catalog Manager em Desenvolvimento" -ForegroundColor Green
Write-Host ""

# Verificar se .env existe
if (-not (Test-Path .env)) {
    Write-Host "❌ Arquivo .env não encontrado!" -ForegroundColor Red
    Write-Host "📝 Criando .env a partir do .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  IMPORTANTE: Edite o arquivo .env e adicione suas chaves GROQ_API_KEYS" -ForegroundColor Yellow
    Write-Host ""
}

# Verificar se frontend/.env.local existe
if (-not (Test-Path frontend/.env.local)) {
    Write-Host "📝 Criando frontend/.env.local..." -ForegroundColor Yellow
    @"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=admin123
"@ | Out-File -FilePath frontend/.env.local -Encoding utf8
    Write-Host "✅ frontend/.env.local criado" -ForegroundColor Green
    Write-Host ""
}

Write-Host "🐘 Subindo PostgreSQL, Redis e MinIO..." -ForegroundColor Cyan
docker-compose up -d postgres redis minio

Write-Host ""
Write-Host "⏳ Aguardando serviços iniciarem (10 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "🔄 Rodando migrations..." -ForegroundColor Cyan
docker-compose run --rm api alembic upgrade head

Write-Host ""
Write-Host "🚀 Subindo Backend API..." -ForegroundColor Green
Write-Host "   URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
docker-compose up api
