# Script de Diagnóstico do Frontend - SixPet Catalog Engine (PowerShell)

Write-Host "🔍 Diagnóstico do Frontend - SixPet Catalog Engine" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Verificar se o container está rodando
Write-Host "📊 Status do Container Frontend:" -ForegroundColor Cyan
$containerStatus = docker ps | Select-String "sixpet-catalog-frontend"
if ($containerStatus) {
    Write-Host $containerStatus -ForegroundColor Green
} else {
    Write-Host "❌ Container não encontrado" -ForegroundColor Red
}

# Verificar logs do container
Write-Host ""
Write-Host "📋 Logs Recentes do Frontend (últimas 50 linhas):" -ForegroundColor Cyan
try {
    docker logs --tail 50 sixpet-catalog-frontend
} catch {
    Write-Host "❌ Não foi possível obter logs" -ForegroundColor Red
}

# Verificar saúde do container
Write-Host ""
Write-Host "🏥 Health Check do Container:" -ForegroundColor Cyan
try {
    $healthStatus = docker inspect sixpet-catalog-frontend --format='{{.State.Health.Status}}'
    Write-Host $healthStatus -ForegroundColor Green
} catch {
    Write-Host "❌ Health check não disponível" -ForegroundColor Red
}

# Testar conectividade
Write-Host ""
Write-Host "🌐 Teste de Conectividade:" -ForegroundColor Cyan

Write-Host "Frontend (interno):" -ForegroundColor White
try {
    docker exec sixpet-catalog-frontend curl -f http://localhost:3000/api/health | Out-Null
    Write-Host "✅ OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Falhou" -ForegroundColor Red
}

Write-Host "Frontend (externo):" -ForegroundColor White
try {
    Invoke-WebRequest -Uri "https://catalog.sxconnect.com.br/api/health" -UseBasicParsing | Out-Null
    Write-Host "✅ OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Falhou" -ForegroundColor Red
}

Write-Host "Backend API:" -ForegroundColor White
try {
    Invoke-WebRequest -Uri "https://catalog-api.sxconnect.com.br/health" -UseBasicParsing | Out-Null
    Write-Host "✅ OK" -ForegroundColor Green
} catch {
    Write-Host "❌ Falhou" -ForegroundColor Red
}

# Verificar variáveis de ambiente
Write-Host ""
Write-Host "🔧 Variáveis de Ambiente do Frontend:" -ForegroundColor Cyan
try {
    docker exec sixpet-catalog-frontend env | Select-String -Pattern "(NEXT_|NODE_|API_)"
} catch {
    Write-Host "❌ Não foi possível obter variáveis" -ForegroundColor Red
}

# Verificar recursos do container
Write-Host ""
Write-Host "💻 Recursos do Container:" -ForegroundColor Cyan
try {
    docker stats --no-stream sixpet-catalog-frontend
} catch {
    Write-Host "❌ Não foi possível obter estatísticas" -ForegroundColor Red
}

# Verificar imagem
Write-Host ""
Write-Host "🐳 Informações da Imagem:" -ForegroundColor Cyan
try {
    $imageInfo = docker inspect sixpet-catalog-frontend --format='{{.Config.Image}}'
    Write-Host $imageInfo -ForegroundColor Green
} catch {
    Write-Host "❌ Não foi possível obter informações da imagem" -ForegroundColor Red
}

# Verificar rede
Write-Host ""
Write-Host "🌐 Configuração de Rede:" -ForegroundColor Cyan
try {
    $ipAddress = docker inspect sixpet-catalog-frontend --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
    Write-Host $ipAddress -ForegroundColor Green
} catch {
    Write-Host "❌ Não foi possível obter IP" -ForegroundColor Red
}

# Verificar labels do Traefik
Write-Host ""
Write-Host "🏷️ Labels do Traefik:" -ForegroundColor Cyan
try {
    $labels = docker inspect sixpet-catalog-frontend --format='{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}' | Select-String "traefik"
    if ($labels) {
        Write-Host $labels -ForegroundColor Green
    } else {
        Write-Host "❌ Labels não encontrados" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Labels não encontrados" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Diagnóstico concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Comandos úteis:" -ForegroundColor Cyan
Write-Host "   Reiniciar: docker restart sixpet-catalog-frontend" -ForegroundColor White
Write-Host "   Logs em tempo real: docker logs -f sixpet-catalog-frontend" -ForegroundColor White
Write-Host "   Entrar no container: docker exec -it sixpet-catalog-frontend sh" -ForegroundColor White
Write-Host "   Rebuild: docker-compose -f docker-compose.prod.yml up -d --force-recreate frontend" -ForegroundColor White