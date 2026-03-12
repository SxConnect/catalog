#!/bin/bash

#===============================================================================
# SCRIPT DE BACKUP MELHORADO - VPS
# Backup automático de volumes Docker e configurações
#===============================================================================

# Configurações
BACKUP_DIR="/root/backup"
LOG_FILE="/var/log/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"
CONFIG_BACKUP="$BACKUP_DIR/config_$DATE.tar.gz"
RETENTION_DAYS=7

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

#===============================================================================
# FUNÇÕES UTILITÁRIAS
#===============================================================================

# Função de log
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

# Verificar se Docker está rodando
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker não está rodando!"
        exit 1
    fi
}

# Criar diretório de backup
create_backup_dir() {
    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        log "Diretório de backup criado: $BACKUP_DIR"
    fi
}

# Verificar espaço em disco
check_disk_space() {
    local available=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local required=1048576  # 1GB em KB
    
    if [ "$available" -lt "$required" ]; then
        log_warning "Pouco espaço em disco disponível: $(($available/1024))MB"
    fi
}

#===============================================================================
# FUNÇÕES DE BACKUP
#===============================================================================

# Backup dos volumes Docker
backup_volumes() {
    log "Iniciando backup dos volumes Docker..."
    
    # Lista de volumes para backup
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
    
    # Construir comando docker run com todos os volumes
    local docker_cmd="docker run --rm"
    local tar_paths=""
    
    for volume in "${volumes[@]}"; do
        # Verificar se o volume existe
        if docker volume inspect "${volume%%:*}" >/dev/null 2>&1; then
            docker_cmd="$docker_cmd -v $volume"
            tar_paths="$tar_paths /${volume##*:}"
        else
            log_warning "Volume não encontrado: ${volume%%:*}"
        fi
    done
    
    # Adicionar volume de backup
    docker_cmd="$docker_cmd -v $BACKUP_DIR:/backup alpine"
    
    # Executar backup
    if eval "$docker_cmd tar czf /backup/backup_$DATE.tar.gz $tar_paths" 2>>"$LOG_FILE"; then
        if [ -f "$BACKUP_FILE" ]; then
            local backup_size=$(du -h "$BACKUP_FILE" | cut -f1)
            log_success "Backup dos volumes criado: $BACKUP_FILE ($backup_size)"
            return 0
        else
            log_error "Arquivo de backup não foi criado"
            return 1
        fi
    else
        log_error "Falha ao executar backup dos volumes"
        return 1
    fi
}

# Backup das configurações
backup_configs() {
    log "Iniciando backup das configurações..."
    
    local config_paths=(
        "/root/portainer"
        "/root/stacks"
        "/root/backup_script.sh"
        "/root/dev-catalog"
    )
    
    local existing_paths=""
    for path in "${config_paths[@]}"; do
        if [ -e "$path" ]; then
            existing_paths="$existing_paths $path"
        else
            log_warning "Caminho não encontrado: $path"
        fi
    done
    
    if [ -n "$existing_paths" ]; then
        if tar czf "$CONFIG_BACKUP" $existing_paths 2>>"$LOG_FILE"; then
            local config_size=$(du -h "$CONFIG_BACKUP" | cut -f1)
            log_success "Backup das configurações criado: $CONFIG_BACKUP ($config_size)"
            return 0
        else
            log_error "Falha ao criar backup das configurações"
            return 1
        fi
    else
        log_warning "Nenhuma configuração encontrada para backup"
        return 1
    fi
}

# Limpeza de backups antigos
cleanup_old_backups() {
    log "Limpando backups antigos (retenção: $RETENTION_DAYS dias)..."
    
    # Remover backups de volumes antigos
    local old_backups=$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null)
    if [ -n "$old_backups" ]; then
        echo "$old_backups" | xargs rm -f
        local count=$(echo "$old_backups" | wc -l)
        log "Removidos $count backups de volumes antigos"
    fi
    
    # Remover backups de configuração antigos
    local old_configs=$(find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +$RETENTION_DAYS 2>/dev/null)
    if [ -n "$old_configs" ]; then
        echo "$old_configs" | xargs rm -f
        local count=$(echo "$old_configs" | wc -l)
        log "Removidos $count backups de configuração antigos"
    fi
}

# Verificar integridade do backup
verify_backup() {
    log "Verificando integridade do backup..."
    
    if [ -f "$BACKUP_FILE" ]; then
        if tar tzf "$BACKUP_FILE" >/dev/null 2>&1; then
            log_success "Backup dos volumes está íntegro"
        else
            log_error "Backup dos volumes está corrompido!"
            return 1
        fi
    fi
    
    if [ -f "$CONFIG_BACKUP" ]; then
        if tar tzf "$CONFIG_BACKUP" >/dev/null 2>&1; then
            log_success "Backup das configurações está íntegro"
        else
            log_error "Backup das configurações está corrompido!"
            return 1
        fi
    fi
    
    return 0
}

# Gerar relatório do backup
generate_report() {
    local total_backups=$(ls -1 "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)
    local total_configs=$(ls -1 "$BACKUP_DIR"/config_*.tar.gz 2>/dev/null | wc -l)
    local total_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)
    
    log "=== RELATÓRIO DO BACKUP ==="
    log "Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')"
    log "Backups de volumes: $total_backups"
    log "Backups de configuração: $total_configs"
    log "Tamanho total: $total_size"
    log "Diretório: $BACKUP_DIR"
    log "=========================="
}

#===============================================================================
# EXECUÇÃO PRINCIPAL
#===============================================================================

main() {
    log "=== INICIANDO BACKUP AUTOMÁTICO ==="
    
    # Verificações iniciais
    check_docker
    create_backup_dir
    check_disk_space
    
    # Executar backups
    local backup_success=true
    
    if ! backup_volumes; then
        backup_success=false
    fi
    
    if ! backup_configs; then
        log_warning "Backup de configurações falhou, mas continuando..."
    fi
    
    # Verificar integridade
    if ! verify_backup; then
        backup_success=false
    fi
    
    # Limpeza
    cleanup_old_backups
    
    # Relatório final
    generate_report
    
    if [ "$backup_success" = true ]; then
        log_success "Backup concluído com sucesso!"
        exit 0
    else
        log_error "Backup concluído com erros!"
        exit 1
    fi
}

# Executar apenas se chamado diretamente
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi