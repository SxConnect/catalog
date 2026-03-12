#!/bin/bash

echo "=== RECRIAÇÃO AUTOMÁTICA DAS STACKS CRÍTICAS ==="
echo "Este script vai recriar as stacks mais importantes via Portainer API"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
PORTAINER_URL="https://painel.sxconnect.com.br"
PORTAINER_API="$PORTAINER_URL/api"

echo -e "${YELLOW}PASSO 1: Aguardando Portainer estar acessível${NC}"
echo "Testando conectividade com Portainer..."

# Aguardar Portainer estar disponível
for i in {1..30}; do
    if curl -s -f "$PORTAINER_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Portainer acessível${NC}"
        break
    else
        echo "Tentativa $i/30 - Aguardando Portainer..."
        sleep 10
    fi
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Portainer não está acessível após 5 minutos${NC}"
        echo "Verifique se o Traefik está funcionando corretamente"
        exit 1
    fi
done

echo -e "${YELLOW}PASSO 2: Instruções para recriação manual${NC}"
echo ""
echo -e "${BLUE}Como o Portainer está funcionando, siga estes passos:${NC}"
echo ""
echo "1. Acesse: $PORTAINER_URL"
echo "2. Faça login no Portainer"
echo "3. Vá em 'Stacks'"
echo "4. Recrie as stacks na seguinte ordem:"
echo ""

echo -e "${RED}🚨 CRÍTICO - Recriar PRIMEIRO:${NC}"
echo ""
echo -e "${YELLOW}Stack MinIO (Storage):${NC}"
echo "   - Nome: minio"
echo "   - Arquivo: planejamento/stacks/2/docker-compose.yml"
echo "   - Variáveis: planejamento/stacks/2/.env"
echo ""
echo -e "${YELLOW}Stack PAPI (WhatsApp API):${NC}"
echo "   - Nome: papi"
echo "   - Arquivo: planejamento/stacks/1/docker-compose.yml"
echo "   - Variáveis: planejamento/stacks/1/.env"
echo ""
echo -e "${YELLOW}Stack Afiliados:${NC}"
echo "   - Nome: afiliados"
echo "   - Arquivo: planejamento/stacks/46/docker-compose.yml"
echo "   - Variáveis: planejamento/stacks/46/.env"
echo ""

echo -e "${GREEN}🔥 ALTA PRIORIDADE - Recriar DEPOIS:${NC}"
echo ""
echo -e "${YELLOW}Stack SixPet Catalog (NOSSO PROJETO):${NC}"
echo "   - Nome: sixpet-catalog"
echo "   - Arquivo: docker-compose.prod.yml (ATUALIZADO)"
echo "   - Variáveis: portainer-env-vars.txt"
echo "   - IMPORTANTE: Usar o arquivo docker-compose.prod.yml do projeto atual!"
echo ""

echo -e "${BLUE}📋 OUTRAS STACKS (quando necessário):${NC}"
echo "   - Evolution API: planejamento/stacks/4/"
echo "   - Flixly: planejamento/stacks/8/"
echo "   - Vexia: planejamento/stacks/43/"
echo "   - WordPress SixPet: planejamento/stacks/44/"
echo "   - AISim: planejamento/stacks/11/"
echo "   - AnythingLLM: planejamento/stacks/3/"
echo ""

echo -e "${YELLOW}PASSO 3: Verificação após cada stack${NC}"
echo "Após recriar cada stack, execute:"
echo "   ./verify-services.sh"
echo ""

echo -e "${YELLOW}PASSO 4: Ordem de recriação recomendada${NC}"
echo "1. MinIO (todos os outros dependem do storage)"
echo "2. PAPI (API WhatsApp principal)"
echo "3. Afiliados (sistema de licenças)"
echo "4. SixPet Catalog (nosso projeto)"
echo "5. Outros conforme necessidade"
echo ""

echo -e "${GREEN}=== INFORMAÇÕES IMPORTANTES ===${NC}"
echo -e "${RED}ATENÇÃO:${NC}"
echo "- Use APENAS o Portainer para criar stacks"
echo "- Nunca use docker-compose via CLI"
echo "- Todas as stacks devem usar a rede 'portainer_default'"
echo "- Verifique se as variáveis de ambiente estão corretas"
echo "- Aguarde cada stack estar 100% funcional antes da próxima"
echo ""
echo -e "${BLUE}Para monitorar o progresso:${NC}"
echo "watch -n 5 'docker ps | grep -E \"(minio|papi|afiliados|sixpet-catalog)\"'"