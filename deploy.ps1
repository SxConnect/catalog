# Deploy Script para SixPet Catalog Engine (PowerShell)
# Usa imagens do GitHub Container Registry

Write-Host "🚀 Iniciando deploy do SixPet Catalog Engine..." -ForegroundColor Green

# Verificar se o arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "❌ Arquivo .env não encontrado!" -ForegroundColor Red
    Write-Host "📝 Copie o .env.prod.example para .env e configure as variáveis:" -ForegroundColor Yellow
    Write-Host "   Copy-Item .env.prod.example .env" -ForegroundColor Cyan
    exit 1
}

# Parar containers existentes
Write-Host "🛑 Parando containers existentes..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml down

# Fazer pull das imagens mais recentes
Write-Host "📥 Baixando imagens mais recentes do GHCR..." -ForegroundColor Blue
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Subir os serviços
Write-Host "🔄 Iniciando serviços..." -ForegroundColor Blue
docker-compose -f docker-compose.prod.yml up -d

# Aguardar o banco de dados estar pronto
Write-Host "⏳ Aguardando banco de dados..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Executar migrações
Write-Host "🗄️ Executando migrações do banco de dados..." -ForegroundColor Blue
docker exec sixpet-catalog-api alembic upgrade head

# Verificar status dos containers
Write-Host "📊 Status dos containers:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

# Verificar logs
Write-Host "📋 Últimos logs do backend:" -ForegroundColor Cyan
docker logs --tail 20 sixpet-catalog-api

Write-Host "📋 Últimos logs do frontend:" -ForegroundColor Cyan
docker logs --tail 20 sixpet-catalog-frontend

Write-Host "✅ Deploy concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs de acesso:" -ForegroundColor Cyan
Write-Host "   Frontend: https://catalog.sxconnect.com.br" -ForegroundColor White
Write-Host "   Backend API: https://catalog-api.sxconnect.com.br" -ForegroundColor White
Write-Host "   Documentação: https://catalog-api.sxconnect.com.br/docs" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   Ver logs: docker logs -f sixpet-catalog-api" -ForegroundColor White
Write-Host "   Reiniciar: docker restart sixpet-catalog-api" -ForegroundColor White
Write-Host "   Parar tudo: docker-compose -f docker-compose.prod.yml down" -ForegroundColor White