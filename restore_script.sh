#!/bin/bash

#===============================================================================
# SCRIPT DE RESTAURAÇÃO - VPS
# Restaura backups de volumes Docker e configurações
#===============================================================================

# Configurações
BACKUP_DIR="/root/backup"
LOG_FILE="/var/log/restore.log"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#===============================================================================
# FUNÇÕES UTILITÁRIAS
#===============================================================================

print_header() {
    clear
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                    RESTAURAÇÃO DE BACKUP                         ║"
    echo "║                     VPS Recovery Tool                            ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    local message="$(date '+%Y-%m-%d %H:%M:%S') - $1"
    echo -e "$message" | tee -a "$LOG_FILE"
}

log_success() {
    log "${GREEN}✔ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠ $1${NC}"
}

log_error() {
    log "${RED}✖ $1${NC}"
}

# Verificar se é root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Execute como root: sudo ./restore_script.sh"
        exit 1
    fi
}

# Verificar se Docker está rodando
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker não está rodando!"
        exit 1
    fi
}

#===============================================================================
# FUNÇÕES DE LISTAGEM
#===============================================================================

list_backups() {
    echo -e "\n${BLUE}=== BACKUPS DISPONÍVEIS ===${NC}"
    
    local backups=($(ls -1t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null))
    
    if [ ${#backups[@]} -eq 0 ]; then
        log_error "Nenhum backup encontrado em $BACKUP_DIR"
        exit 1
    fi
    
    echo -e "\n${YELLOW}Backups de Volumes:${NC}"
    for i in "${!backups[@]}"; do
        local backup="${backups[$i]}"
        local size=$(du -h "$backup" | cut -f1)
        local date=$(basename "$backup" | sed 's/backup_\(.*\)\.tar\.gz/\1/')
        local formatted_date=$(echo "$date" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
        
        printf "%2d) %s (%s) - %s\n" $((i+1)) "$(basename "$backup")" "$size" "$formatted_date"
    done
    
    # Listar backups de configuração
    local configs=($(ls -1t "$BACKUP_DIR"/config_*.tar.gz 2>/dev/null))
    if [ ${#configs[@]} -gt 0 ]; then
        echo -e "\n${YELLOW}Backups de Configuração:${NC}"
        for config in "${configs[@]}"; do
            local size=$(du -h "$config" | cut -f1)
            local date=$(basename "$config" | sed 's/config_\(.*\)\.tar\.gz/\1/')
            local formatted_date=$(echo "$date" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)_\([0-9]\{2\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3 \4:\5:\6/')
            
            printf "   %s (%s) - %s\n" "$(basename "$config")" "$size" "$formatted_date"
        done
    fi
    
    echo "${backups[@]}"
}

#===============================================================================
# FUNÇÕES DE RESTAURAÇÃO
#===============================================================================

select_backup() {
    local backups=($1)
    
    echo -e "\n${BLUE}Selecione o backup para restaurar:${NC}"
    read -p "Digite o número do backup [1-${#backups[@]}]: " backup_num
    
    if ! [[ "$backup_num" =~ ^[0-9]+$ ]] || [ "$backup_num" -lt 1 ] || [ "$backup_num" -gt ${#backups[@]} ]; then
        log_error "Seleção inválida!"
        exit 1
    fi
    
    echo "${backups[$((backup_num-1))]}"
}

verify_backup_integrity() {
    local backup_file="$1"
    
    log "Verificando integridade do backup..."
    
    if ! tar tzf "$backup_file" >/dev/null 2>&1; then
        log_error "Backup está corrompido: $backup_file"
        exit 1
    fi
    
    log_success "Backup está íntegro"
}

show_backup_contents() {
    local backup_file="$1"
    
    echo -e "\n${BLUE}=== CONTEÚDO DO BACKUP ===${NC}"
    tar tzf "$backup_file" | head -20
    
    local total_files=$(tar tzf "$backup_file" | wc -l)
    if [ "$total_files" -gt 20 ]; then
        echo "... e mais $((total_files-20)) arquivos"
    fi
    
    echo -e "\nTotal de arquivos: $total_files"
}

confirm_restore() {
    local backup_file="$1"
    
    echo -e "\n${RED}⚠ ATENÇÃO: OPERAÇÃO DESTRUTIVA ⚠${NC}"
    echo -e "${YELLOW}Esta operação vai:${NC}"
    echo "1. Parar TODOS os containers Docker"
    echo "2. Substituir os volumes existentes"
    echo "3. Os dados atuais serão PERDIDOS"
    echo ""
    echo -e "Backup selecionado: ${BLUE}$(basename "$backup_file")${NC}"
    echo ""
    
    read -p "Tem certeza que deseja continuar? Digite 'CONFIRMO' para prosseguir: " confirmation
    
    if [ "$confirmation" != "CONFIRMO" ]; then
        log "Restauração cancelada pelo usuário"
        exit 0
    fi
}

stop_containers() {
    log "Parando todos os containers..."
    
    local containers=$(docker ps -q)
    if [ -n "$containers" ]; then
        docker stop $containers 2>/dev/null
        log_success "Containers parados"
    else
        log "Nenhum container rodando"
    fi
}

restore_volumes() {
    local backup_file="$1"
    
    log "Iniciando restauração dos volumes..."
    
    # Lista de volumes que podem ser restaurados
    local volumes=(
        "portainer_data:/portainer_data"
        "evolution_data:/evolution_data"
        "evolution_postgres_data:/evolution_postgres_data"
        "papi_sessions:/papi_sessions"
        "papi_postgres_data:/papi_postgres_data"
        "anythingllm_storage:/anythingllm_storage"
        "minio_data:/minio_data"
        "afiliados_postgres_data:/afiliados_postgres_data"
        "afiliados_redis_data:/afiliados_redis_data"
        "flixly_postgres_data:/flixly_postgres_data"
        "flixly_redis_data:/flixly_redis_data"
        "vexia_postgres_data:/vexia_postgres_data"
    )
    
    # Construir comando docker run
    local docker_cmd="docker run --rm"
    
    for volume in "${volumes[@]}"; do
        local volume_name="${volume%%:*}"
        # Criar volume se não existir
        docker volume create "$volume_name" >/dev/null 2>&1
        docker_cmd="$docker_cmd -v $volume"
    done
    
    # Adicionar volume de backup
    docker_cmd="$docker_cmd -v $BACKUP_DIR:/backup alpine"
    
    # Executar restauração
    if eval "$docker_cmd tar xzf /backup/$(basename "$backup_file") -C /" 2>>"$LOG_FILE"; then
        log_success "Volumes restaurados com sucesso"
        return 0
    else
        log_error "Falha na restauração dos volumes"
        return 1
    fi
}

restore_configs() {
    local backup_date="$1"
    local config_file="$BACKUP_DIR/config_${backup_date}.tar.gz"
    
    if [ -f "$config_file" ]; then
        log "Restaurando configurações..."
        
        if tar xzf "$config_file" -C / 2>>"$LOG_FILE"; then
            log_success "Configurações restauradas"
        else
            log_warning "Falha na restauração das configurações"
        fi
    else
        log_warning "Backup de configurações não encontrado: $config_file"
    fi
}

post_restore_instructions() {
    echo -e "\n${GREEN}=== RESTAURAÇÃO CONCLUÍDA ===${NC}"
    echo -e "\n${BLUE}Próximos passos:${NC}"
    echo "1. Acesse o Portainer: https://seu-dominio-portainer"
    echo "2. Verifique se todas as stacks estão funcionando"
    echo "3. Inicie os containers que não iniciaram automaticamente"
    echo "4. Verifique os logs dos serviços"
    echo ""
    echo -e "${YELLOW}Comandos úteis:${NC}"
    echo "docker ps                    # Ver containers rodando"
    echo "docker logs <container>      # Ver logs de um container"
    echo "docker-compose up -d         # Iniciar stack (se necessário)"
    echo ""
}

#===============================================================================
# EXECUÇÃO PRINCIPAL
#===============================================================================

main() {
    print_header
    
    # Verificações iniciais
    check_root
    check_docker
    
    log "=== INICIANDO PROCESSO DE RESTAURAÇÃO ==="
    
    # Listar e selecionar backup
    local backups_array=($(list_backups))
    local selected_backup=$(select_backup "${backups_array[*]}")
    
    # Verificar integridade
    verify_backup_integrity "$selected_backup"
    
    # Mostrar conteúdo
    show_backup_contents "$selected_backup"
    
    # Confirmar operação
    confirm_restore "$selected_backup"
    
    # Executar restauração
    stop_containers
    
    if restore_volumes "$selected_backup"; then
        # Tentar restaurar configurações também
        local backup_date=$(basename "$selected_backup" | sed 's/backup_\(.*\)\.tar\.gz/\1/')
        restore_configs "$backup_date"
        
        log_success "Restauração concluída com sucesso!"
        post_restore_instructions
    else
        log_error "Restauração falhou!"
        exit 1
    fi
}

# Executar
main "$@"