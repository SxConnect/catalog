Write-Host "🔍 Verificando se imagens v1.0.0 estão disponíveis no GHCR..." -ForegroundColor Cyan
Write-Host ""

# Verificar backend
Write-Host "📦 Backend (catalog:1.0.0):" -ForegroundColor Yellow
try {
    docker pull ghcr.io/sxconnect/catalog:1.0.0 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Imagem disponível!" -ForegroundColor Green
    } else {
        Write-Host "❌ Imagem ainda não disponível. Aguarde o build completar." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erro ao verificar imagem." -ForegroundColor Red
}

Write-Host ""

# Verificar frontend
Write-Host "📦 Frontend (catalog-frontend:1.0.0):" -ForegroundColor Yellow
try {
    docker pull ghcr.io/sxconnect/catalog-frontend:1.0.0 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Imagem disponível!" -ForegroundColor Green
    } else {
        Write-Host "❌ Imagem ainda não disponível. Aguarde o build completar." -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Erro ao verificar imagem." -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 Status dos builds: https://github.com/SxConnect/catalog/actions" -ForegroundColor Cyan
