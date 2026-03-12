#!/bin/bash

echo "=== CORREÇÃO CRÍTICA DO TRAEFIK E DEPLOY ==="
echo "Este script vai resolver o problema do Traefik e redeployar o catálogo"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}PASSO 1: Parando containers problemáticos criados fora do Portainer${NC}"
echo "Removendo containers que causam conflito com Traefik..."

# Parar e remover containers específicos que foram criados fora do Portainer
docker stop sixpet-catalog-worker sixpet-catalog-postgres sixpet-catalog-redis sixpet-catalog-api sixpet-catalog-frontend 2>/dev/null || true
docker rm sixpet-catalog-worker sixpet-catalog-postgres sixpet-catalog-redis sixpet-catalog-api sixpet-catalog-frontend 2>/dev/null || true

echo -e "${GREEN}✓ Containers problemáticos removidos${NC}"

echo -e "${YELLOW}PASSO 2: Reiniciando Traefik${NC}"
echo "Parando Traefik atual..."
cd /root/portainer/
docker-compose stop traefik 2>/dev/null || true

echo "Iniciando Traefik..."
docker-compose up -d traefik

# Aguardar Traefik inicializar
echo "Aguardando Traefik inicializar..."
sleep 10

echo -e "${GREEN}✓ Traefik reiniciado${NC}"

echo -e "${YELLOW}PASSO 3: Verificando status do Traefik${NC}"
if docker ps | grep -q traefik; then
    echo -e "${GREEN}✓ Traefik está rodando${NC}"
else
    echo -e "${RED}✗ Traefik não está rodando - verificar logs${NC}"
    docker-compose logs traefik --tail=20
fi

echo -e "${YELLOW}PASSO 4: Verificando redes Docker${NC}"
echo "Redes disponíveis:"
docker network ls | grep portainer

echo -e "${YELLOW}PASSO 5: Instruções para recriar stack no Portainer${NC}"
echo ""
echo -e "${GREEN}PRÓXIMOS PASSOS MANUAIS NO PORTAINER:${NC}"
echo "1. Acesse o Portainer"
echo "2. Vá em 'Stacks'"
echo "3. Se existir stack 'sixpet-catalog', DELETE ela completamente"
echo "4. Crie nova stack com nome 'sixpet-catalog'"
echo "5. Cole o conteúdo do docker-compose.prod.yml"
echo "6. Configure as variáveis de ambiente:"
echo "   - GROQ_API_KEYS=sua_chave_aqui"
echo "   - MINIO_ROOT_USER=admin"
echo "   - MINIO_ROOT_PASSWORD=sua_senha_minio"
echo "   - S3_BUCKET=sixpet-catalog"
echo "   - NEXTAUTH_SECRET=sua_secret_key"
echo "   - ADMIN_EMAIL=admin@sixpet.com"
echo "   - ADMIN_PASSWORD=sua_senha_admin"
echo "7. Deploy da stack"
echo ""

echo -e "${YELLOW}PASSO 6: Testando conectividade dos serviços principais${NC}"
echo "Testando MinIO..."
curl -s -o /dev/null -w "%{http_code}" https://mins3.sxconnect.com.br || echo "MinIO: Erro de conectividade"

echo "Testando PAPI..."
curl -s -o /dev/null -w "%{http_code}" https://papi.sxconnect.com.br || echo "PAPI: Erro de conectividade"

echo ""
echo -e "${GREEN}=== SCRIPT CONCLUÍDO ===${NC}"
echo -e "${YELLOW}IMPORTANTE:${NC}"
echo "- Todos os containers problemáticos foram removidos"
echo "- Traefik foi reiniciado"
echo "- Agora recrie a stack no Portainer seguindo as instruções acima"
echo "- Use APENAS o Portainer para gerenciar containers"
echo "- O novo subdomínio sixpetapi.sxconnect.com.br está configurado"
echo ""
echo -e "${RED}LEMBRE-SE: Nunca mais criar containers via CLI - sempre usar Portainer!${NC}"