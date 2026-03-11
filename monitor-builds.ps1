# Script para monitorar builds do GitHub Actions (PowerShell)

Write-Host "🔍 Monitorando builds do GitHub Actions..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# URLs dos workflows
$BACKEND_WORKFLOW = "https://github.com/SxConnect/catalog/actions/workflows/docker-publish.yml"
$FRONTEND_WORKFLOW = "https://github.com/SxConnect/catalog/actions/workflows/docker-publish-frontend.yml"

Write-Host "🔗 Links dos workflows:" -ForegroundColor Cyan
Write-Host "   Backend:  $BACKEND_WORKFLOW" -ForegroundColor White
Write-Host "   Frontend: $FRONTEND_WORKFLOW" -ForegroundColor White
Write-Host ""

# Verificar se as imagens estão disponíveis no GHCR
Write-Host "🐳 Verificando imagens no GHCR..." -ForegroundColor Cyan

Write-Host "Backend:" -ForegroundColor White
try {
    docker pull ghcr.io/sxconnect/catalog-backend:latest | Out-Null
    Write-Host "✅ ghcr.io/sxconnect/catalog-backend:latest - Disponível" -ForegroundColor Green
} catch {
    Write-Host "⏳ ghcr.io/sxconnect/catalog-backend:latest - Aguardando build..." -ForegroundColor Yellow
}

Write-Host "Frontend:" -ForegroundColor White
try {
    docker pull ghcr.io/sxconnect/catalog-frontend:latest | Out-Null
    Write-Host "✅ ghcr.io/sxconnect/catalog-frontend:latest - Disponível" -ForegroundColor Green
} catch {
    Write-Host "⏳ ghcr.io/sxconnect/catalog-frontend:latest - Aguardando build..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Para acompanhar o progresso:" -ForegroundColor Cyan
Write-Host "   1. Acesse: https://github.com/SxConnect/catalog/actions" -ForegroundColor White
Write-Host "   2. Aguarde os builds completarem (ícones verdes)" -ForegroundColor White
Write-Host "   3. Execute: ./update-production.sh na VPS" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Para verificar novamente, execute: ./monitor-builds.ps1" -ForegroundColor Cyan