#!/bin/bash

# Script para monitorar build da correção de AuthenticationError
# Versão: v1.0.9-auth-fix

echo "🔍 Monitorando build da correção de AuthenticationError..."
echo "📋 Tag: v1.0.9-auth-fix"
echo "🐳 Imagem: ghcr.io/sxconnect/catalog-backend:v1.0.9-auth-fix"
echo ""

# Função para verificar se a imagem existe
check_image() {
    echo "🔍 Verificando se a imagem está disponível..."
    
    # Tentar fazer pull da imagem
    if docker pull ghcr.io/sxconnect/catalog-backend:v1.0.9-auth-fix >/dev/null 2>&1; then
        echo "✅ Imagem disponível no GHCR!"
        return 0
    else
        echo "⏳ Imagem ainda não disponível..."
        return 1
    fi
}

# Função para mostrar instruções de deploy
show_deploy_instructions() {
    echo ""
    echo "🚀 INSTRUÇÕES DE DEPLOY:"
    echo "1. Acessar Portainer"
    echo "2. Ir em Stacks → catalog-stack"
    echo "3. Clicar em 'Update the stack'"
    echo "4. MARCAR: 'Re-pull image and redeploy'"
    echo "5. Clicar em 'Update'"
    echo ""
    echo "📊 Monitorar logs após deploy:"
    echo "docker logs sixpet-catalog-api -f"
    echo ""
    echo "✅ Logs esperados:"
    echo "- INFO: Security middleware configured successfully"
    echo "- INFO: Rate limiting configured successfully"
    echo "- INFO: Security headers configured successfully"
    echo ""
}

# Loop de monitoramento
attempt=1
max_attempts=30  # 30 tentativas = ~15 minutos

while [ $attempt -le $max_attempts ]; do
    echo "🔄 Tentativa $attempt/$max_attempts..."
    
    if check_image; then
        echo ""
        echo "🎉 BUILD CONCLUÍDO COM SUCESSO!"
        show_deploy_instructions
        
        # Perguntar se deve fazer deploy automaticamente
        echo "❓ Fazer deploy automaticamente? (y/n)"
        read -t 10 -n 1 response
        echo ""
        
        if [[ $response == "y" || $response == "Y" ]]; then
            echo "🚀 Iniciando deploy automático..."
            echo "⚠️  ATENÇÃO: Certifique-se de que o Portainer está acessível"
            echo "📋 Arquivo docker-compose.prod.yml já foi atualizado"
            echo ""
            echo "🔧 Para deploy manual:"
            echo "1. Copie o conteúdo de docker-compose.prod.yml"
            echo "2. Cole no Portainer Stack Editor"
            echo "3. Marque 'Re-pull image and redeploy'"
            echo "4. Clique em 'Update'"
        fi
        
        exit 0
    fi
    
    # Aguardar 30 segundos antes da próxima tentativa
    echo "⏳ Aguardando 30 segundos..."
    sleep 30
    
    attempt=$((attempt + 1))
done

echo ""
echo "⚠️  TIMEOUT: Build não concluído em 15 minutos"
echo "🔍 Verificar manualmente:"
echo "   https://github.com/SxConnect/catalog/actions"
echo ""
echo "🔄 Para tentar novamente:"
echo "   ./monitor-build-auth-fix.sh"