#!/bin/bash

#===============================================================================
# INSTALADOR AUTOMÁTICO - VPS SETUP
# Portainer + Traefik + Evolution + PAPI + AnythingLLM + MinIO
#===============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Diretórios
PORTAINER_DIR="/root/portainer"
BACKUP_DIR="/root/backup"
STACKS_DIR="/root/stacks"
REPORT_FILE="$PORTAINER_DIR/instalacao_relatorio.txt"

#===============================================================================
# FUNÇÕES UTILITÁRIAS
#===============================================================================

print_header() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    INSTALADOR VPS AUTOMÁTICO                     ║"
    echo "║         Portainer • Evolution • PAPI • AnythingLLM • MinIO       ║"
    echo "║                                                                  ║"
    echo "║                    SxConnect by Silvano Xavier                   ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✔ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✖ $1${NC}"
}

# Gerar senha segura (12 caracteres: maiúscula, minúscula, número, especial)
generate_password() {
    local password=""
    local uppercase="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    local lowercase="abcdefghijklmnopqrstuvwxyz"
    local numbers="0123456789"
    local special="@#$%&*!?"
    local all="${uppercase}${lowercase}${numbers}${special}"
    
    # Garantir pelo menos 1 de cada tipo
    password+="${uppercase:RANDOM%${#uppercase}:1}"
    password+="${lowercase:RANDOM%${#lowercase}:1}"
    password+="${numbers:RANDOM%${#numbers}:1}"
    password+="${special:RANDOM%${#special}:1}"
    
    # Completar com caracteres aleatórios
    for i in {1..8}; do
        password+="${all:RANDOM%${#all}:1}"
    done
    
    # Embaralhar a senha
    echo "$password" | fold -w1 | shuf | tr -d '\n'
}

# Gerar API Key (32 caracteres hexadecimais)
generate_api_key() {
    openssl rand -hex 16 | tr '[:lower:]' '[:upper:]'
}

# Perguntar imagem Docker
ask_image() {
    local service_name=$1
    local default_image=$2
    local image_var=$3
    
    echo -e "\n${CYAN}Qual imagem do $service_name deseja usar?${NC}"
    echo "1) latest"
    echo "2) Outra (digite a versão)"
    read -p "Escolha [1/2]: " choice
    
    if [ "$choice" == "2" ]; then
        read -p "Digite a imagem completa (ex: $default_image): " custom_image
        eval "$image_var='$custom_image'"
    else
        eval "$image_var='${default_image%:*}:latest'"
    fi
}

#===============================================================================
# VERIFICAÇÃO E PREPARAÇÃO DA VPS
#===============================================================================

check_vps() {
    print_header
    print_step "Verificando estado da VPS..."
    
    # Verificar se é root
    if [ "$EUID" -ne 0 ]; then
        print_error "Execute como root: sudo ./install.sh"
        exit 1
    fi
    
    # Verificar se Docker está instalado
    if command -v docker &> /dev/null; then
        print_warning "Docker já está instalado"
        
        # Verificar containers existentes
        CONTAINERS=$(docker ps -aq 2>/dev/null | wc -l)
        if [ "$CONTAINERS" -gt 0 ]; then
            print_warning "Encontrados $CONTAINERS containers existentes"
            echo -e "\n${YELLOW}Deseja limpar tudo e começar do zero?${NC}"
            echo "1) Sim, apagar tudo"
            echo "2) Não, manter e continuar"
            echo "3) Cancelar instalação"
            read -p "Escolha [1/2/3]: " clean_choice
            
            case $clean_choice in
                1)
                    print_step "Limpando ambiente..."
                    docker stop $(docker ps -aq) 2>/dev/null || true
                    docker rm $(docker ps -aq) 2>/dev/null || true
                    docker network prune -f 2>/dev/null || true
                    docker volume prune -f 2>/dev/null || true
                    print_success "Ambiente limpo"
                    ;;
                2)
                    print_warning "Mantendo containers existentes"
                    ;;
                3)
                    print_error "Instalação cancelada"
                    exit 0
                    ;;
            esac
        fi
    else
        print_step "Instalando Docker..."
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
        print_success "Docker instalado"
    fi
    
    # Verificar backups existentes
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        print_warning "Backups encontrados em $BACKUP_DIR"
        echo -e "\n${YELLOW}Deseja restaurar de um backup?${NC}"
        echo "1) Sim, restaurar backup"
        echo "2) Não, instalação limpa"
        read -p "Escolha [1/2]: " backup_choice
        
        if [ "$backup_choice" == "1" ]; then
            RESTORE_BACKUP=true
            ls -la $BACKUP_DIR
            read -p "Digite o nome do arquivo de backup: " BACKUP_FILE
        fi
    fi
}

#===============================================================================
# COLETA DE INFORMAÇÕES
#===============================================================================

collect_info() {
    print_header
    print_step "Coletando informações para instalação..."
    
    # Email para SSL
    echo -e "\n${CYAN}═══ CONFIGURAÇÃO GERAL ═══${NC}"
    read -p "Email para certificados SSL: " SSL_EMAIL
    
    # Portainer
    echo -e "\n${CYAN}═══ PORTAINER ═══${NC}"
    read -p "Domínio do Portainer (ex: painel.seudominio.com.br): " PORTAINER_DOMAIN
    
    # Evolution
    echo -e "\n${CYAN}═══ EVOLUTION API ═══${NC}"
    read -p "Domínio da Evolution (ex: evo.seudominio.com.br): " EVOLUTION_DOMAIN
    ask_image "Evolution" "evoapicloud/evolution-api:v2.3.0" "EVOLUTION_IMAGE"
    
    # PAPI
    echo -e "\n${CYAN}═══ PAPI (Pastorini API) ═══${NC}"
    read -p "Domínio da PAPI (ex: papi.seudominio.com.br): " PAPI_DOMAIN
    ask_image "PAPI" "intrategica/papi-free:1.5.2" "PAPI_IMAGE"
    read -p "LICENSE_KEY da PAPI: " PAPI_LICENSE_KEY
    
    # AnythingLLM
    echo -e "\n${CYAN}═══ ANYTHINGLLM ═══${NC}"
    read -p "Domínio do AnythingLLM (ex: llm.seudominio.com.br): " ANYTHINGLLM_DOMAIN
    ask_image "AnythingLLM" "mintplexlabs/anythingllm:latest" "ANYTHINGLLM_IMAGE"
    
    # MinIO
    echo -e "\n${CYAN}═══ MINIO ═══${NC}"
    echo -e "${YELLOW}Escolha o tipo de instalação do MinIO:${NC}"
    echo "1) MinIO Completo (API S3 + Console Web + Buckets automáticos)"
    echo "2) MinIO Simples (Apenas API S3 + Console básico)"
    read -p "Escolha [1/2]: " MINIO_TYPE
    
    case $MINIO_TYPE in
        1)
            MINIO_SETUP="complete"
            echo -e "${GREEN}✔ MinIO Completo selecionado${NC}"
            ;;
        2)
            MINIO_SETUP="simple"
            echo -e "${GREEN}✔ MinIO Simples selecionado${NC}"
            ;;
        *)
            print_warning "Opção inválida, usando MinIO Completo"
            MINIO_SETUP="complete"
            ;;
    esac
    
    read -p "Domínio do Console MinIO (ex: minio.seudominio.com.br): " MINIO_CONSOLE_DOMAIN
    read -p "Domínio do S3 MinIO (ex: s3.seudominio.com.br): " MINIO_S3_DOMAIN
    ask_image "MinIO" "quay.io/minio/minio:latest" "MINIO_IMAGE"
    
    # Gerar senhas
    print_step "Gerando senhas seguras..."
    POSTGRES_PASSWORD=$(generate_password)
    REDIS_PASSWORD=$(generate_password)
    MINIO_PASSWORD=$(generate_password)
    EVOLUTION_API_KEY=$(generate_api_key)
    PAPI_PANEL_KEY=$(generate_api_key)
    
    print_success "Informações coletadas"
}

#===============================================================================
# CRIAR ESTRUTURA DE DIRETÓRIOS
#===============================================================================

create_directories() {
    print_step "Criando estrutura de diretórios..."
    
    mkdir -p $PORTAINER_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p $STACKS_DIR/evolution
    mkdir -p $STACKS_DIR/papi
    mkdir -p $STACKS_DIR/anythingllm
    mkdir -p $STACKS_DIR/minio
    
    # Criar acme.json com permissões corretas
    touch $PORTAINER_DIR/acme.json
    chmod 600 $PORTAINER_DIR/acme.json
    
    print_success "Diretórios criados"
}

#===============================================================================
# CRIAR REDE
#===============================================================================

create_network() {
    print_step "Criando rede Docker..."
    
    docker network create portainer_default 2>/dev/null || true
    
    print_success "Rede portainer_default criada"
}

#===============================================================================
# INSTALAR TRAEFIK
#===============================================================================

install_traefik() {
    print_step "Instalando Traefik..."
    
    docker rm -f traefik 2>/dev/null || true
    
    docker run -d \
        --name traefik \
        --restart always \
        --network portainer_default \
        -p 80:80 \
        -p 443:443 \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v $PORTAINER_DIR/acme.json:/acme.json \
        traefik:latest \
        --entrypoints.web.address=:80 \
        --entrypoints.websecure.address=:443 \
        --providers.docker=true \
        --providers.docker.exposedbydefault=false \
        --providers.docker.network=portainer_default \
        --certificatesresolvers.leresolver.acme.httpchallenge=true \
        --certificatesresolvers.leresolver.acme.httpchallenge.entrypoint=web \
        --certificatesresolvers.leresolver.acme.email=$SSL_EMAIL \
        --certificatesresolvers.leresolver.acme.storage=/acme.json \
        --log.level=ERROR \
        --api.dashboard=false
    
    print_success "Traefik instalado"
}

#===============================================================================
# INSTALAR PORTAINER
#===============================================================================

install_portainer() {
    print_step "Instalando Portainer..."
    
    docker rm -f portainer 2>/dev/null || true
    
    docker run -d \
        --name portainer \
        --restart always \
        --network portainer_default \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        --label "traefik.enable=true" \
        --label "traefik.http.routers.portainer.rule=Host(\`$PORTAINER_DOMAIN\`)" \
        --label "traefik.http.routers.portainer.entrypoints=websecure" \
        --label "traefik.http.routers.portainer.tls.certresolver=leresolver" \
        --label "traefik.http.services.portainer.loadbalancer.server.port=9000" \
        portainer/portainer-ce:latest
    
    print_success "Portainer instalado"
}

#===============================================================================
# CRIAR STACK EVOLUTION
#===============================================================================

create_evolution_stack() {
    print_step "Criando stack Evolution..."
    
    # Criar .env
    cat > $STACKS_DIR/evolution/.env << EOF
# Evolution API - Configurações
EVOLUTION_IMAGE=$EVOLUTION_IMAGE
EVOLUTION_DOMAIN=$EVOLUTION_DOMAIN
EVOLUTION_API_KEY=$EVOLUTION_API_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
REDIS_PASSWORD=$REDIS_PASSWORD

# S3/MinIO (opcional)
S3_ENABLED=false
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=evolution
S3_ENDPOINT=$MINIO_S3_DOMAIN
EOF

    # Criar docker-compose.yml
    cat > $STACKS_DIR/evolution/docker-compose.yml << 'EOF'
version: "3.8"

services:
  evolution:
    image: ${EVOLUTION_IMAGE}
    restart: always
    networks:
      - portainer_default
    volumes:
      - evolution_data:/app/data
    environment:
      - SERVER_URL=https://${EVOLUTION_DOMAIN}
      - AUTHENTICATION_API_KEY=${EVOLUTION_API_KEY}
      - AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true
      - LANGUAGE=pt-BR
      - DEL_INSTANCE=false
      - DATABASE_PROVIDER=postgresql
      - DATABASE_CONNECTION_URI=postgresql://postgres:${POSTGRES_PASSWORD}@evolution_postgres:5432/evolution?schema=public
      - DATABASE_SAVE_DATA_INSTANCE=true
      - DATABASE_SAVE_DATA_NEW_MESSAGE=true
      - DATABASE_SAVE_MESSAGE_UPDATE=true
      - DATABASE_SAVE_DATA_CONTACTS=true
      - DATABASE_SAVE_DATA_CHATS=true
      - DATABASE_SAVE_DATA_LABELS=true
      - DATABASE_SAVE_DATA_HISTORIC=true
      - DATABASE_CONNECTION_CLIENT_NAME=evolution
      - WEBHOOK_GLOBAL_ENABLED=false
      - WEBHOOK_EVENTS_QRCODE_UPDATED=true
      - WEBHOOK_EVENTS_MESSAGES_UPSERT=true
      - WEBHOOK_EVENTS_MESSAGES_UPDATE=true
      - WEBHOOK_EVENTS_SEND_MESSAGE=true
      - WEBHOOK_EVENTS_CONNECTION_UPDATE=true
      - CONFIG_SESSION_PHONE_CLIENT=Evolution API
      - CONFIG_SESSION_PHONE_NAME=Chrome
      - QRCODE_LIMIT=30
      - OPENAI_ENABLED=true
      - DIFY_ENABLED=true
      - TYPEBOT_ENABLED=true
      - CACHE_REDIS_URI=redis://:${REDIS_PASSWORD}@evolution_redis:6379/1
      - CACHE_LOCAL_ENABLED=true
      - CACHE_REDIS_PREFIX_KEY=evolution
      - CACHE_REDIS_SAVE_INSTANCES=false
    labels:
      - traefik.enable=true
      - traefik.http.routers.evolution.rule=Host(`${EVOLUTION_DOMAIN}`)
      - traefik.http.routers.evolution.entrypoints=websecure
      - traefik.http.routers.evolution.tls.certresolver=leresolver
      - traefik.http.services.evolution.loadbalancer.server.port=8080
    depends_on:
      - evolution_postgres
      - evolution_redis
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  evolution_postgres:
    image: postgres:15-alpine
    restart: always
    networks:
      - portainer_default
    volumes:
      - evolution_postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=evolution
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

  evolution_redis:
    image: redis:alpine
    restart: always
    networks:
      - portainer_default
    volumes:
      - evolution_redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

volumes:
  evolution_data:
  evolution_postgres_data:
  evolution_redis_data:

networks:
  portainer_default:
    external: true
EOF

    print_success "Stack Evolution criada em $STACKS_DIR/evolution"
}

#===============================================================================
# CRIAR STACK PAPI
#===============================================================================

create_papi_stack() {
    print_step "Criando stack PAPI..."
    
    # Criar .env
    cat > $STACKS_DIR/papi/.env << EOF
# PAPI - Configurações
PAPI_IMAGE=$PAPI_IMAGE
PAPI_DOMAIN=$PAPI_DOMAIN
PAPI_LICENSE_KEY=$PAPI_LICENSE_KEY
PAPI_PANEL_KEY=$PAPI_PANEL_KEY
PAPI_POSTGRES_PASSWORD=$POSTGRES_PASSWORD
EOF

    # Criar docker-compose.yml
    cat > $STACKS_DIR/papi/docker-compose.yml << 'EOF'
version: "3.8"

services:
  papi:
    image: ${PAPI_IMAGE}
    restart: always
    networks:
      - portainer_default
    volumes:
      - papi_sessions:/app/sessions
      - papi_media:/app/Media
    environment:
      - NODE_ENV=production
      - PORT=3000
      - PANEL_API_KEY=${PAPI_PANEL_KEY}
      - STORAGE_TYPE=postgres+redis
      - POSTGRES_HOST=papi_postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=papi
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${PAPI_POSTGRES_PASSWORD}
      - POSTGRES_SSL=false
      - REDIS_HOST=papi_redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=
      - REDIS_DB=0
      - LICENSE_KEY=${PAPI_LICENSE_KEY}
      - LICENSE_ADMIN_URL=https://padmin.intrategica.com.br
    labels:
      - traefik.enable=true
      - traefik.http.routers.papi.rule=Host(`${PAPI_DOMAIN}`)
      - traefik.http.routers.papi.entrypoints=websecure
      - traefik.http.routers.papi.tls.certresolver=leresolver
      - traefik.http.services.papi.loadbalancer.server.port=3000
    depends_on:
      - papi_postgres
      - papi_redis

  papi_postgres:
    image: postgres:13-alpine
    restart: always
    networks:
      - portainer_default
    volumes:
      - papi_postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=papi
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${PAPI_POSTGRES_PASSWORD}

  papi_redis:
    image: redis:alpine
    restart: always
    networks:
      - portainer_default
    volumes:
      - papi_redis_data:/data
    command: redis-server --appendonly yes

volumes:
  papi_sessions:
  papi_media:
  papi_postgres_data:
  papi_redis_data:

networks:
  portainer_default:
    external: true
EOF

    print_success "Stack PAPI criada em $STACKS_DIR/papi"
}

#===============================================================================
# CRIAR STACK ANYTHINGLLM
#===============================================================================

create_anythingllm_stack() {
    print_step "Criando stack AnythingLLM..."
    
    # Criar .env
    cat > $STACKS_DIR/anythingllm/.env << EOF
# AnythingLLM - Configurações
ANYTHINGLLM_IMAGE=$ANYTHINGLLM_IMAGE
ANYTHINGLLM_DOMAIN=$ANYTHINGLLM_DOMAIN
EOF

    # Criar docker-compose.yml
    cat > $STACKS_DIR/anythingllm/docker-compose.yml << 'EOF'
version: "3.8"

services:
  anythingllm:
    image: ${ANYTHINGLLM_IMAGE}
    restart: always
    networks:
      - portainer_default
    volumes:
      - anythingllm_storage:/app/server/storage
    environment:
      - STORAGE_DIR=/app/server/storage
      - UID=1000
      - GID=1000
    labels:
      - traefik.enable=true
      - traefik.http.routers.anythingllm.rule=Host(`${ANYTHINGLLM_DOMAIN}`)
      - traefik.http.routers.anythingllm.entrypoints=websecure
      - traefik.http.routers.anythingllm.tls.certresolver=leresolver
      - traefik.http.services.anythingllm.loadbalancer.server.port=3001

volumes:
  anythingllm_storage:

networks:
  portainer_default:
    external: true
EOF

    print_success "Stack AnythingLLM criada em $STACKS_DIR/anythingllm"
}

#===============================================================================
# CRIAR STACK MINIO
#===============================================================================

create_minio_stack() {
    if [ "$MINIO_SETUP" == "complete" ]; then
        create_minio_complete_stack
    else
        create_minio_simple_stack
    fi
}

create_minio_complete_stack() {
    print_step "Criando stack MinIO Completo..."
    
    # Criar .env
    cat > $STACKS_DIR/minio/.env << EOF
# MinIO - Configurações Completas
MINIO_IMAGE=$MINIO_IMAGE
MINIO_CONSOLE_DOMAIN=$MINIO_CONSOLE_DOMAIN
MINIO_S3_DOMAIN=$MINIO_S3_DOMAIN
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=$MINIO_PASSWORD
EOF

    # Criar docker-compose.yml
    cat > $STACKS_DIR/minio/docker-compose.yml << 'EOF'
version: "3.8"

services:
  minio:
    image: ${MINIO_IMAGE}
    restart: always
    command: server /data --console-address ":9001"
    networks:
      - portainer_default
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
      - MINIO_BROWSER_REDIRECT_URL=https://${MINIO_CONSOLE_DOMAIN}
      - MINIO_SERVER_URL=https://${MINIO_S3_DOMAIN}
    labels:
      # API S3 (porta 9000)
      - traefik.enable=true
      - traefik.http.routers.minio_s3.rule=Host(`${MINIO_S3_DOMAIN}`)
      - traefik.http.routers.minio_s3.entrypoints=websecure
      - traefik.http.routers.minio_s3.tls.certresolver=leresolver
      - traefik.http.routers.minio_s3.service=minio_s3
      - traefik.http.services.minio_s3.loadbalancer.server.port=9000
      - traefik.http.services.minio_s3.loadbalancer.passHostHeader=true
      # Console Web (porta 9001)
      - traefik.http.routers.minio_console.rule=Host(`${MINIO_CONSOLE_DOMAIN}`)
      - traefik.http.routers.minio_console.entrypoints=websecure
      - traefik.http.routers.minio_console.tls.certresolver=leresolver
      - traefik.http.routers.minio_console.service=minio_console
      - traefik.http.services.minio_console.loadbalancer.server.port=9001
      - traefik.http.services.minio_console.loadbalancer.passHostHeader=true

  # Serviço para criar buckets automaticamente
  minio-setup:
    image: minio/mc:latest
    depends_on:
      - minio
    networks:
      - portainer_default
    entrypoint: >
      /bin/sh -c "
      sleep 10;
      /usr/bin/mc alias set myminio http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD};
      /usr/bin/mc mb myminio/sixpet-catalog --ignore-existing;
      /usr/bin/mc mb myminio/evolution --ignore-existing;
      /usr/bin/mc mb myminio/papi --ignore-existing;
      /usr/bin/mc mb myminio/afiliados --ignore-existing;
      /usr/bin/mc mb myminio/flixly --ignore-existing;
      /usr/bin/mc policy set public myminio/sixpet-catalog;
      echo 'Buckets criados com sucesso';
      exit 0;
      "

volumes:
  minio_data:

networks:
  portainer_default:
    external: true
EOF

    print_success "Stack MinIO Completo criada em $STACKS_DIR/minio"
}

create_minio_simple_stack() {
    print_step "Criando stack MinIO Simples..."
    
    # Criar .env
    cat > $STACKS_DIR/minio/.env << EOF
# MinIO - Configurações Simples
MINIO_IMAGE=$MINIO_IMAGE
MINIO_CONSOLE_DOMAIN=$MINIO_CONSOLE_DOMAIN
MINIO_S3_DOMAIN=$MINIO_S3_DOMAIN
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=$MINIO_PASSWORD
EOF

    # Criar docker-compose.yml (versão que estava rodando)
    cat > $STACKS_DIR/minio/docker-compose.yml << 'EOF'
version: "3.8"
services:
  minio:
    image: ${MINIO_IMAGE}
    restart: always
    command: server /data --console-address ":9001"
    networks:
      - portainer_default
    volumes:
      - minio_data:/data
    environment:
      - MINIO_ROOT_USER=${MINIO_ROOT_USER}
      - MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
      - MINIO_BROWSER_REDIRECT_URL=https://${MINIO_CONSOLE_DOMAIN}
      - MINIO_SERVER_URL=https://${MINIO_S3_DOMAIN}
    labels:
      - traefik.enable=true
      # API / S3
      - traefik.http.routers.minio_public.rule=Host(`${MINIO_S3_DOMAIN}`)
      - traefik.http.routers.minio_public.entrypoints=websecure
      - traefik.http.routers.minio_public.tls.certresolver=leresolver
      - traefik.http.routers.minio_public.service=minio_public
      - traefik.http.services.minio_public.loadbalancer.server.port=9000
      # Console
      - traefik.http.routers.minio_console.rule=Host(`${MINIO_CONSOLE_DOMAIN}`)
      - traefik.http.routers.minio_console.entrypoints=websecure
      - traefik.http.routers.minio_console.tls.certresolver=leresolver
      - traefik.http.routers.minio_console.service=minio_console
      - traefik.http.services.minio_console.loadbalancer.server.port=9001

volumes:
  minio_data:

networks:
  portainer_default:
    external: true
EOF

    print_success "Stack MinIO Simples criada em $STACKS_DIR/minio"
}

#===============================================================================
# CONFIGURAR BACKUP AUTOMÁTICO
#===============================================================================

setup_backup() {
    print_step "Configurando backup automático..."
    
    # Criar script de backup
    cat > /root/backup_script.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# Criar backup dos volumes
docker run --rm \
    -v portainer_data:/portainer_data \
    -v evolution_data:/evolution_data \
    -v evolution_postgres_data:/evolution_postgres_data \
    -v papi_sessions:/papi_sessions \
    -v papi_postgres_data:/papi_postgres_data \
    -v anythingllm_storage:/anythingllm_storage \
    -v minio_data:/minio_data \
    -v $BACKUP_DIR:/backup \
    alpine tar czf /backup/backup_$DATE.tar.gz \
        /portainer_data \
        /evolution_data \
        /evolution_postgres_data \
        /papi_sessions \
        /papi_postgres_data \
        /anythingllm_storage \
        /minio_data \
    2>/dev/null

# Manter apenas os últimos 7 backups
ls -t $BACKUP_DIR/backup_*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null

echo "Backup criado: $BACKUP_FILE"
EOF

    chmod +x /root/backup_script.sh
    
    # Adicionar ao cron (meia-noite)
    (crontab -l 2>/dev/null | grep -v backup_script; echo "0 0 * * * /root/backup_script.sh") | crontab -
    
    print_success "Backup automático configurado (00:00 diariamente)"
}

#===============================================================================
# GERAR RELATÓRIO
#===============================================================================

generate_report() {
    print_step "Gerando relatório de instalação..."
    
    cat > $REPORT_FILE << EOF
╔══════════════════════════════════════════════════════════════════════════════╗
║                        RELATÓRIO DE INSTALAÇÃO                               ║
║                        $(date '+%Y-%m-%d %H:%M:%S')                              ║
║                                                                              ║
║                        SxConnect by Silvano Xavier                           ║
╚══════════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
                              PORTAINER
═══════════════════════════════════════════════════════════════════════════════
URL:        https://$PORTAINER_DOMAIN
Usuário:    (criar no primeiro acesso)
Senha:      (criar no primeiro acesso)

═══════════════════════════════════════════════════════════════════════════════
                              EVOLUTION API
═══════════════════════════════════════════════════════════════════════════════
URL:        https://$EVOLUTION_DOMAIN
Imagem:     $EVOLUTION_IMAGE
API Key:    $EVOLUTION_API_KEY
Postgres:   postgres / $POSTGRES_PASSWORD
Redis:      $REDIS_PASSWORD

═══════════════════════════════════════════════════════════════════════════════
                              PAPI (Pastorini API)
═══════════════════════════════════════════════════════════════════════════════
URL:        https://$PAPI_DOMAIN
Imagem:     $PAPI_IMAGE
Panel Key:  $PAPI_PANEL_KEY
License:    $PAPI_LICENSE_KEY
Postgres:   postgres / $POSTGRES_PASSWORD

═══════════════════════════════════════════════════════════════════════════════
                              ANYTHINGLLM
═══════════════════════════════════════════════════════════════════════════════
URL:        https://$ANYTHINGLLM_DOMAIN
Imagem:     $ANYTHINGLLM_IMAGE

═══════════════════════════════════════════════════════════════════════════════
                              MINIO
═══════════════════════════════════════════════════════════════════════════════
Tipo:       $([ "$MINIO_SETUP" == "complete" ] && echo "Completo (com buckets automáticos)" || echo "Simples (apenas storage)")
Console:    https://$MINIO_CONSOLE_DOMAIN
S3 API:     https://$MINIO_S3_DOMAIN
Imagem:     $MINIO_IMAGE
Usuário:    admin
Senha:      $MINIO_PASSWORD
$([ "$MINIO_SETUP" == "complete" ] && echo "Buckets:    sixpet-catalog, evolution, papi, afiliados, flixly" || echo "Buckets:    Criar manualmente via console")

═══════════════════════════════════════════════════════════════════════════════
                              DIRETÓRIOS
═══════════════════════════════════════════════════════════════════════════════
Portainer:  $PORTAINER_DIR
Stacks:     $STACKS_DIR
Backups:    $BACKUP_DIR
Relatório:  $REPORT_FILE

═══════════════════════════════════════════════════════════════════════════════
                              PRÓXIMOS PASSOS
═══════════════════════════════════════════════════════════════════════════════
1. Acesse o Portainer: https://$PORTAINER_DOMAIN
2. Crie sua conta de administrador
3. Vá em Stacks > Add Stack
4. Para cada serviço, faça upload do docker-compose.yml e .env:
   - Evolution: $STACKS_DIR/evolution/
   - PAPI:      $STACKS_DIR/papi/
   - AnythingLLM: $STACKS_DIR/anythingllm/
   - MinIO:     $STACKS_DIR/minio/ ($([ "$MINIO_SETUP" == "complete" ] && echo "Completo" || echo "Simples"))

$([ "$MINIO_SETUP" == "complete" ] && echo "5. MinIO Completo: Buckets serão criados automaticamente após deploy" || echo "5. MinIO Simples: Crie buckets manualmente via console conforme necessário")

═══════════════════════════════════════════════════════════════════════════════
                              BACKUP
═══════════════════════════════════════════════════════════════════════════════
Backup automático configurado para 00:00 diariamente
Local: $BACKUP_DIR
Retenção: 7 dias

EOF

    chmod 600 $REPORT_FILE
    print_success "Relatório salvo em $REPORT_FILE"
}

#===============================================================================
# EXIBIR RESUMO FINAL
#===============================================================================

show_summary() {
    print_header
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    INSTALAÇÃO CONCLUÍDA!                         ║"
    echo "║                                                                  ║"
    echo "║                    SxConnect by Silvano Xavier                   ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "\n${CYAN}═══ ACESSOS ═══${NC}"
    echo -e "Portainer:    ${GREEN}https://$PORTAINER_DOMAIN${NC}"
    echo -e "Evolution:    ${GREEN}https://$EVOLUTION_DOMAIN${NC}"
    echo -e "PAPI:         ${GREEN}https://$PAPI_DOMAIN${NC}"
    echo -e "AnythingLLM:  ${GREEN}https://$ANYTHINGLLM_DOMAIN${NC}"
    echo -e "MinIO Console:${GREEN}https://$MINIO_CONSOLE_DOMAIN${NC} ($([ "$MINIO_SETUP" == "complete" ] && echo "Completo" || echo "Simples"))"
    echo -e "MinIO S3 API: ${GREEN}https://$MINIO_S3_DOMAIN${NC}"
    
    echo -e "\n${CYAN}═══ CREDENCIAIS ═══${NC}"
    echo -e "Evolution API Key: ${YELLOW}$EVOLUTION_API_KEY${NC}"
    echo -e "PAPI Panel Key:    ${YELLOW}$PAPI_PANEL_KEY${NC}"
    echo -e "MinIO User:        ${YELLOW}admin${NC}"
    echo -e "MinIO Password:    ${YELLOW}$MINIO_PASSWORD${NC}"
    
    echo -e "\n${CYAN}═══ CONFIGURAÇÃO MINIO ═══${NC}"
    if [ "$MINIO_SETUP" == "complete" ]; then
        echo -e "Tipo: ${GREEN}Completo${NC} - Buckets criados automaticamente"
        echo -e "Buckets: ${YELLOW}sixpet-catalog, evolution, papi, afiliados, flixly${NC}"
    else
        echo -e "Tipo: ${GREEN}Simples${NC} - Apenas storage básico"
        echo -e "Buckets: ${YELLOW}Criar manualmente conforme necessário${NC}"
    fi
    
    echo -e "\n${CYAN}═══ ARQUIVOS ═══${NC}"
    echo -e "Relatório completo: ${YELLOW}$REPORT_FILE${NC}"
    echo -e "Stacks editáveis:   ${YELLOW}$STACKS_DIR${NC}"
    
    echo -e "\n${YELLOW}⚠ IMPORTANTE:${NC}"
    echo "1. Aguarde ~2 minutos para os certificados SSL serem gerados"
    echo "2. Acesse o Portainer e crie sua conta admin"
    echo "3. Importe as stacks de $STACKS_DIR no Portainer"
    echo ""
}

#===============================================================================
# EXECUÇÃO PRINCIPAL
#===============================================================================

main() {
    check_vps
    collect_info
    create_directories
    create_network
    install_traefik
    install_portainer
    create_evolution_stack
    create_papi_stack
    create_anythingllm_stack
    create_minio_stack
    setup_backup
    generate_report
    show_summary
}

# Executar
main
