# Deploy Guide - SixPet Catalog Engine

## 🚀 Deploy Automático via GitHub Actions

### 1. Configurar Secrets no GitHub

Acesse: `Settings > Secrets and variables > Actions`

Não é necessário adicionar secrets! O workflow usa `GITHUB_TOKEN` automaticamente.

### 2. Push para Main

```bash
git push origin main
```

O GitHub Actions irá:
1. Build da imagem Docker
2. Push para `ghcr.io/sxconnect/catalog:latest`
3. Criar tags automáticas (branch, sha, version)

### 3. Verificar Build

Acesse: `Actions` tab no GitHub

A imagem estará disponível em:
```
ghcr.io/sxconnect/catalog:latest
ghcr.io/sxconnect/catalog:main
ghcr.io/sxconnect/catalog:main-<sha>
```

## 📦 Deploy na VPS (Portainer)

### 1. Preparar Ambiente

```bash
# Criar diretório
mkdir -p /opt/sixpet-catalog
cd /opt/sixpet-catalog

# Baixar docker-compose
curl -O https://raw.githubusercontent.com/SxConnect/catalog/main/docker-compose.prod.yml

# Criar .env
cp .env.prod.example .env
nano .env  # Editar com credenciais reais
```

### 2. Configurar .env

```env
# Database
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=SuaSenhaForte123!
POSTGRES_DB=sixpet_catalog

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=SuaSenhaForte456!
S3_BUCKET=sixpet-catalog
STORAGE_TYPE=minio

# Groq API Keys
GROQ_API_KEYS=gsk_sua_key_1,gsk_sua_key_2,gsk_sua_key_3
```

### 3. Deploy via Portainer

#### Opção A: Via Portainer UI

1. Acesse Portainer
2. Stacks > Add Stack
3. Nome: `sixpet-catalog`
4. Upload: `docker-compose.prod.yml`
5. Environment variables: Cole conteúdo do `.env`
6. Deploy

#### Opção B: Via CLI

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verificar Deploy

```bash
# Verificar containers
docker ps | grep sixpet-catalog

# Logs da API
docker logs sixpet-catalog-api -f

# Logs do Worker
docker logs sixpet-catalog-worker -f

# Health check
curl https://catalog-api.sxconnect.com.br/health
```

## 🌐 URLs de Acesso

Após deploy, os serviços estarão disponíveis em:

- **API:** https://catalog-api.sxconnect.com.br
- **API Docs:** https://catalog-api.sxconnect.com.br/docs
- **MinIO Console:** https://minio.catalog.sxconnect.com.br
- **MinIO API:** https://minio-api.catalog.sxconnect.com.br

## 🔄 Atualizar Aplicação

### Método 1: Pull Nova Imagem

```bash
# Pull nova versão
docker pull ghcr.io/sxconnect/catalog:latest

# Restart services
docker-compose -f docker-compose.prod.yml up -d --force-recreate api worker
```

### Método 2: Via Portainer

1. Stacks > sixpet-catalog
2. Editor > Pull and redeploy
3. Update the stack

### Método 3: Webhook (Recomendado)

Configure webhook no Portainer para auto-deploy:

1. Portainer > Stacks > sixpet-catalog > Webhook
2. Copy webhook URL
3. GitHub > Settings > Webhooks > Add webhook
4. Paste URL
5. Events: `push` to `main`

Agora cada push no GitHub fará deploy automático!

## 🗄️ Migrations

### Primeira Instalação

```bash
# Entrar no container
docker exec -it sixpet-catalog-api bash

# Rodar migrations
alembic upgrade head

# Sair
exit
```

### Atualizar Schema

```bash
docker exec -it sixpet-catalog-api alembic upgrade head
```

## 🔐 Configurar MinIO

### 1. Acessar Console

https://minio.catalog.sxconnect.com.br

Login: `minioadmin` / `sua_senha`

### 2. Criar Bucket

1. Buckets > Create Bucket
2. Nome: `sixpet-catalog`
3. Access Policy: `Public` (para imagens)

### 3. Configurar CORS (Opcional)

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"]
    }
  ]
}
```

## 📊 Monitoramento

### Logs

```bash
# API
docker logs sixpet-catalog-api -f --tail 100

# Worker
docker logs sixpet-catalog-worker -f --tail 100

# PostgreSQL
docker logs sixpet-catalog-postgres -f --tail 100

# Redis
docker logs sixpet-catalog-redis -f --tail 100
```

### Métricas

```bash
# Status dos containers
docker stats sixpet-catalog-api sixpet-catalog-worker

# Uso de disco
docker system df

# Volumes
docker volume ls | grep sixpet
```

### Health Checks

```bash
# API
curl https://catalog-api.sxconnect.com.br/health

# PostgreSQL
docker exec sixpet-catalog-postgres pg_isready -U sixpet

# Redis
docker exec sixpet-catalog-redis redis-cli ping
```

## 🔧 Troubleshooting

### Container não inicia

```bash
# Ver logs
docker logs sixpet-catalog-api

# Verificar variáveis
docker exec sixpet-catalog-api env | grep DATABASE_URL
```

### Erro de conexão com banco

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Testar conexão
docker exec sixpet-catalog-api psql $DATABASE_URL -c "SELECT 1"
```

### Worker não processa

```bash
# Verificar Redis
docker exec sixpet-catalog-redis redis-cli ping

# Ver fila
docker exec sixpet-catalog-redis redis-cli LLEN celery

# Restart worker
docker restart sixpet-catalog-worker
```

## 🔄 Backup

### Banco de Dados

```bash
# Backup
docker exec sixpet-catalog-postgres pg_dump -U sixpet sixpet_catalog > backup.sql

# Restore
cat backup.sql | docker exec -i sixpet-catalog-postgres psql -U sixpet sixpet_catalog
```

### MinIO

```bash
# Backup bucket
docker exec sixpet-catalog-minio mc mirror /data/sixpet-catalog /backup/

# Restore
docker exec sixpet-catalog-minio mc mirror /backup/ /data/sixpet-catalog
```

## 🚨 Rollback

```bash
# Voltar para versão anterior
docker pull ghcr.io/sxconnect/catalog:main-<commit-sha>

# Atualizar compose para usar tag específica
# Editar docker-compose.prod.yml: image: ghcr.io/sxconnect/catalog:main-<sha>

# Restart
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

## 📈 Escalabilidade

### Adicionar mais Workers

```bash
# Editar docker-compose.prod.yml
# Adicionar worker-2, worker-3, etc.

docker-compose -f docker-compose.prod.yml up -d --scale worker=4
```

### Load Balancer

Traefik já está configurado. Para múltiplas instâncias da API:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale api=3
```

## 🎯 Checklist de Deploy

- [ ] Secrets configurados no GitHub
- [ ] Push para main (build automático)
- [ ] Imagem disponível no GHCR
- [ ] .env configurado na VPS
- [ ] docker-compose.prod.yml baixado
- [ ] Stack criado no Portainer
- [ ] Migrations executadas
- [ ] MinIO bucket criado
- [ ] URLs acessíveis
- [ ] Health checks OK
- [ ] Webhook configurado (opcional)

## 🆘 Suporte

Em caso de problemas:

1. Verificar logs dos containers
2. Testar health checks
3. Verificar variáveis de ambiente
4. Consultar documentação no GitHub
5. Abrir issue: https://github.com/SxConnect/catalog/issues
