# Script de Atualização para VPS - SixPet Catalog Engine (PowerShell)
# Atualiza as imagens do GHCR e reinicia os serviços

Write-Host "🔄 Atualizando SixPet Catalog Engine na VPS..." -ForegroundColor Green

# Verificar se estamos no diretório correto
if (-not (Test-Path "docker-compose.prod.yml")) {
    Write-Host "❌ Arquivo docker-compose.prod.yml não encontrado!" -ForegroundColor Red
    Write-Host "📁 Execute este script no diretório do projeto" -ForegroundColor Yellow
    exit 1
}

# Fazer backup do estado atual
Write-Host "💾 Fazendo backup do estado atual..." -ForegroundColor Blue
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
docker-compose -f docker-compose.prod.yml ps > "backup-status-$timestamp.txt"

# Parar os serviços (mantendo banco e redis rodando)
Write-Host "🛑 Parando serviços da aplicação..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml stop api worker frontend

# Fazer pull das imagens mais recentes
Write-Host "📥 Baixando imagens mais recentes do GHCR..." -ForegroundColor Blue
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Remover containers antigos
Write-Host "🗑️ Removendo containers antigos..." -ForegroundColor Yellow
docker-compose -f docker-compose.prod.yml rm -f api worker frontend

# Subir os serviços atualizados
Write-Host "🚀 Iniciando serviços atualizados..." -ForegroundColor Green
docker-compose -f docker-compose.prod.yml up -d api worker frontend

# Aguardar os serviços estarem prontos
Write-Host "⏳ Aguardando serviços ficarem prontos..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Executar migrações se necessário
Write-Host "🗄️ Verificando migrações do banco de dados..." -ForegroundColor Blue
docker exec sixpet-catalog-api alembic upgrade head

# Verificar status dos serviços
Write-Host "📊 Status dos serviços atualizados:" -ForegroundColor Cyan
docker-compose -f docker-compose.prod.yml ps

# Verificar saúde dos serviços
Write-Host "🏥 Verificando saúde dos serviços..." -ForegroundColor Cyan
Write-Host "Backend API:" -ForegroundColor White
try {
    Invoke-WebRequest -Uri "https://catalog-api.sxconnect.com.br/health" -UseBasicParsing | Out-Null
    Write-Host "✅ Backend OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Backend não respondeu" -ForegroundColor Yellow
}

Write-Host "Frontend:" -ForegroundColor White
try {
    Invoke-WebRequest -Uri "https://catalog.sxconnect.com.br/api/health" -UseBasicParsing | Out-Null
    Write-Host "✅ Frontend OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Frontend não respondeu" -ForegroundColor Yellow
}

# Mostrar logs recentes
Write-Host "📋 Logs recentes do backend:" -ForegroundColor Cyan
docker logs --tail 10 sixpet-catalog-api

Write-Host "📋 Logs recentes do frontend:" -ForegroundColor Cyan
docker logs --tail 10 sixpet-catalog-frontend

Write-Host "✅ Atualização concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 URLs de acesso:" -ForegroundColor Cyan
Write-Host "   Frontend: https://catalog.sxconnect.com.br" -ForegroundColor White
Write-Host "   Backend API: https://catalog-api.sxconnect.com.br" -ForegroundColor White
Write-Host "   Documentação: https://catalog-api.sxconnect.com.br/docs" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   Ver logs: docker logs -f sixpet-catalog-api" -ForegroundColor White
Write-Host "   Reiniciar: docker restart sixpet-catalog-api" -ForegroundColor White
Write-Host "   Status: docker-compose -f docker-compose.prod.yml ps" -ForegroundColor White