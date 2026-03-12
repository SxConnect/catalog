# Melhorias no Sistema de Backup

## Análise do Instalador Atual

O instalador `install.sh` já tem um sistema de backup bem estruturado, mas pode ser melhorado:

### ✅ Pontos Positivos
- Script de backup automático criado em `/root/backup_script.sh`
- Backup configurado no cron para executar diariamente às 00:00
- Retenção de 7 dias (remove backups antigos)
- Backup de todos os volumes importantes:
  - portainer_data
  - evolution_data, evolution_postgres_data
  - papi_sessions, papi_postgres_data
  - anythingllm_storage
  - minio_data

### ⚠️ Melhorias Necessárias

1. **Verificação de Sucesso**: O script não verifica se o backup foi criado com sucesso
2. **Logs**: Não há logs detalhados dos backups
3. **Notificação**: Não há notificação em caso de falha
4. **Teste de Restauração**: Não há script para restaurar backups
5. **Backup das Configurações**: Não faz backup dos arquivos de configuração (.env, docker-compose.yml)

## Script de Backup Melhorado

```bash
#!/bin/bash

# Configurações
BACKUP_DIR="/root/backup"
LOG_FILE="/var/log/backup.log"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"
CONFIG_BACKUP="$BACKUP_DIR/config_$DATE.tar.gz"

# Função de log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

log "Iniciando backup..."

# 1. Backup dos volumes Docker
log "Fazendo backup dos volumes Docker..."
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
    2>>$LOG_FILE

# Verificar se o backup foi criado
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup dos volumes criado com sucesso: $BACKUP_FILE ($BACKUP_SIZE)"
else
    log "ERRO: Falha ao criar backup dos volumes"
    exit 1
fi

# 2. Backup das configurações
log "Fazendo backup das configurações..."
tar czf "$CONFIG_BACKUP" \
    /root/portainer \
    /root/stacks \
    /root/backup_script.sh \
    2>>$LOG_FILE

if [ -f "$CONFIG_BACKUP" ]; then
    CONFIG_SIZE=$(du -h "$CONFIG_BACKUP" | cut -f1)
    log "Backup das configurações criado: $CONFIG_BACKUP ($CONFIG_SIZE)"
else
    log "AVISO: Falha ao criar backup das configurações"
fi

# 3. Limpeza de backups antigos (manter últimos 7)
log "Limpando backups antigos..."
OLD_BACKUPS=$(ls -t $BACKUP_DIR/backup_*.tar.gz 2>/dev/null | tail -n +8)
OLD_CONFIGS=$(ls -t $BACKUP_DIR/config_*.tar.gz 2>/dev/null | tail -n +8)

if [ ! -z "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | xargs rm -f
    log "Backups antigos removidos: $(echo "$OLD_BACKUPS" | wc -l) arquivos"
fi

if [ ! -z "$OLD_CONFIGS" ]; then
    echo "$OLD_CONFIGS" | xargs rm -f
    log "Configurações antigas removidas: $(echo "$OLD_CONFIGS" | wc -l) arquivos"
fi

# 4. Resumo final
TOTAL_BACKUPS=$(ls -1 $BACKUP_DIR/backup_*.tar.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh $BACKUP_DIR | cut -f1)

log "Backup concluído! Total: $TOTAL_BACKUPS backups ($TOTAL_SIZE)"
```

## Script de Restauração

```bash
#!/bin/bash

# Script para restaurar backup
BACKUP_DIR="/root/backup"

echo "=== RESTAURAÇÃO DE BACKUP ==="
echo ""

# Listar backups disponíveis
echo "Backups disponíveis:"
ls -la $BACKUP_DIR/backup_*.tar.gz 2>/dev/null | nl

echo ""
read -p "Digite o número do backup para restaurar: " BACKUP_NUM

BACKUP_FILE=$(ls -1 $BACKUP_DIR/backup_*.tar.gz 2>/dev/null | sed -n "${BACKUP_NUM}p")

if [ -z "$BACKUP_FILE" ]; then
    echo "Backup não encontrado!"
    exit 1
fi

echo "Restaurando: $BACKUP_FILE"
echo ""
echo "ATENÇÃO: Isso vai parar todos os containers e restaurar os dados!"
read -p "Continuar? (y/N): " CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "Cancelado."
    exit 0
fi

# Parar containers
echo "Parando containers..."
docker stop $(docker ps -aq) 2>/dev/null

# Restaurar volumes
echo "Restaurando volumes..."
docker run --rm \
    -v portainer_data:/portainer_data \
    -v evolution_data:/evolution_data \
    -v evolution_postgres_data:/evolution_postgres_data \
    -v papi_sessions:/papi_sessions \
    -v papi_postgres_data:/papi_postgres_data \
    -v anythingllm_storage:/anythingllm_storage \
    -v minio_data:/minio_data \
    -v $BACKUP_DIR:/backup \
    alpine tar xzf /backup/$(basename $BACKUP_FILE) -C /

echo "Restauração concluída!"
echo "Reinicie os containers pelo Portainer."
```

## Implementação das Melhorias

Para implementar essas melhorias na reinstalação da VPS:

1. **Substituir o script de backup** no instalador
2. **Adicionar script de restauração**
3. **Configurar logs rotativos**
4. **Adicionar monitoramento de backup**

Essas melhorias garantem:
- ✅ Backups mais confiáveis
- ✅ Logs detalhados
- ✅ Capacidade de restauração
- ✅ Backup das configurações
- ✅ Monitoramento de falhas