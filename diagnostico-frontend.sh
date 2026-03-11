#!/bin/bash

# Script de Diagnóstico do Frontend - SixPet Catalog Engine

echo "🔍 Diagnóstico do Frontend - SixPet Catalog Engine"
echo "=================================================="

# Verificar se o container está rodando
echo "📊 Status do Container Frontend:"
docker ps | grep sixpet-catalog-frontend || echo "❌ Container não encontrado"

# Verificar logs do container
echo ""
echo "📋 Logs Recentes do Frontend (últimas 50 linhas):"
docker logs --tail 50 sixpet-catalog-frontend 2>/dev/null || echo "❌ Não foi possível obter logs"

# Verificar saúde do container
echo ""
echo "🏥 Health Check do Container:"
docker inspect sixpet-catalog-frontend --format='{{.State.Health.Status}}' 2>/dev/null || echo "❌ Health check não disponível"

# Testar conectividade
echo ""
echo "🌐 Teste de Conectividade:"
echo "Frontend (interno):"
docker exec sixpet-catalog-frontend curl -f http://localhost:3000/api/health 2>/dev/null && echo "✅ OK" || echo "❌ Falhou"

echo "Frontend (externo):"
curl -f https://catalog.sxconnect.com.br/api/health 2>/dev/null && echo "✅ OK" || echo "❌ Falhou"

echo "Backend API:"
curl -f https://catalog-api.sxconnect.com.br/health 2>/dev/null && echo "✅ OK" || echo "❌ Falhou"

# Verificar variáveis de ambiente
echo ""
echo "🔧 Variáveis de Ambiente do Frontend:"
docker exec sixpet-catalog-frontend env | grep -E "(NEXT_|NODE_|API_)" 2>/dev/null || echo "❌ Não foi possível obter variáveis"

# Verificar recursos do container
echo ""
echo "💻 Recursos do Container:"
docker stats --no-stream sixpet-catalog-frontend 2>/dev/null || echo "❌ Não foi possível obter estatísticas"

# Verificar imagem
echo ""
echo "🐳 Informações da Imagem:"
docker inspect sixpet-catalog-frontend --format='{{.Config.Image}}' 2>/dev/null || echo "❌ Não foi possível obter informações da imagem"

# Verificar rede
echo ""
echo "🌐 Configuração de Rede:"
docker inspect sixpet-catalog-frontend --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null || echo "❌ Não foi possível obter IP"

# Verificar labels do Traefik
echo ""
echo "🏷️ Labels do Traefik:"
docker inspect sixpet-catalog-frontend --format='{{range $key, $value := .Config.Labels}}{{$key}}={{$value}}{{"\n"}}{{end}}' 2>/dev/null | grep traefik || echo "❌ Labels não encontrados"

echo ""
echo "✅ Diagnóstico concluído!"
echo ""
echo "🔧 Comandos úteis:"
echo "   Reiniciar: docker restart sixpet-catalog-frontend"
echo "   Logs em tempo real: docker logs -f sixpet-catalog-frontend"
echo "   Entrar no container: docker exec -it sixpet-catalog-frontend sh"
echo "   Rebuild: docker-compose -f docker-compose.prod.yml up -d --force-recreate frontend"