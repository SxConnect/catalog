# 🔧 Troubleshooting - Erros Comuns

## ❌ Erro: password authentication failed for user "sixpet_catalog_user"

### Causa
As variáveis de ambiente do PostgreSQL não estão corretas ou não estão sendo lidas.

### Solução

#### 1. Verificar Variáveis no Portainer

No Portainer, ao editar a stack, certifique-se que as variáveis estão assim:

```env
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=SuaSenhaForte123!
POSTGRES_DB=sixpet_catalog
```

**IMPORTANTE:** O usuário deve ser `sixpet`, NÃO `sixpet_catalog_user`

#### 2. Verificar DATABASE_URL

A `DATABASE_URL` é construída automaticamente no docker-compose:

```yaml
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
```

Deve resultar em:
```
postgresql://sixpet:SuaSenha123!@postgres:5432/sixpet_catalog
```

#### 3. Recriar Banco (se necessário)

Se o banco já foi criado com usuário errado:

```bash
# Parar stack
docker-compose -f docker-compose.prod.yml down

# Remover volume do postgres
docker volume rm catalog_postgres_data

# Subir novamente
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Verificar Dentro do Container

```bash
# Entrar no container da API
docker exec -it sixpet-catalog-api bash

# Ver variáveis
echo $DATABASE_URL
echo $POSTGRES_USER
echo $POSTGRES_PASSWORD

# Testar conexão
psql $DATABASE_URL -c "SELECT 1"
```

---

## ❌ Erro: Invalid endpoint: minio-s3.sxconnect.com.br

### Causa
Endpoint do MinIO sem protocolo `https://`

### Solução

Certifique-se que no Portainer você tem:

```env
MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
```

O código adiciona `https://` automaticamente. Se ainda der erro, force:

```env
S3_ENDPOINT=https://minio-s3.sxconnect.com.br
```

---

## ❌ Erro: Container não inicia

### Verificar Logs

```bash
docker logs sixpet-catalog-api --tail 100
docker logs sixpet-catalog-postgres --tail 100
```

### Verificar Health Checks

```bash
docker ps --filter "name=sixpet-catalog"
```

Se STATUS mostrar `unhealthy`, veja os logs.

---

## ❌ Erro: Bucket não encontrado

### Criar Bucket no MinIO

```bash
# Via CLI
mc alias set myminio https://minio-s3.sxconnect.com.br admin i7uDSxH$smwp
mc mb myminio/sixpet-catalog
mc anonymous set download myminio/sixpet-catalog
```

### Via Console Web

1. https://minio.sxconnect.com.br
2. Buckets > Create Bucket
3. Nome: `sixpet-catalog`
4. Access Policy: Public

---

## ✅ Checklist de Deploy

Antes de fazer deploy, verifique:

- [ ] GitHub Actions build passou (✅ verde)
- [ ] Variáveis de ambiente corretas no Portainer
- [ ] PostgreSQL: `POSTGRES_USER=sixpet`
- [ ] MinIO: Bucket `sixpet-catalog` criado
- [ ] MinIO: Credenciais corretas
- [ ] Groq: API keys válidas
- [ ] Network: `portainer_default` existe

---

## 🔍 Debug Completo

### 1. Verificar Imagem

```bash
docker pull ghcr.io/sxconnect/catalog:latest
docker images | grep catalog
```

### 2. Verificar Network

```bash
docker network ls | grep portainer
docker network inspect portainer_default
```

### 3. Verificar Volumes

```bash
docker volume ls | grep catalog
```

### 4. Testar Conexões

```bash
# PostgreSQL
docker exec sixpet-catalog-postgres pg_isready -U sixpet

# Redis
docker exec sixpet-catalog-redis redis-cli ping

# MinIO (de dentro do container API)
docker exec -it sixpet-catalog-api bash
curl https://minio-s3.sxconnect.com.br
```

### 5. Verificar Variáveis

```bash
docker exec sixpet-catalog-api env | grep -E "DATABASE|REDIS|S3|MINIO|GROQ"
```

---

## 📝 Variáveis Corretas (Exemplo)

```env
# Database
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=MinhaSenhaForte123!
POSTGRES_DB=sixpet_catalog

# MinIO
MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=i7uDSxH$smwp
S3_BUCKET=sixpet-catalog

# Groq
GROQ_API_KEYS=gsk_abc123,gsk_def456
```

---

## 🆘 Ainda com Problemas?

1. Copie os logs completos:
   ```bash
   docker logs sixpet-catalog-api > api-logs.txt
   docker logs sixpet-catalog-postgres > postgres-logs.txt
   ```

2. Verifique as variáveis:
   ```bash
   docker exec sixpet-catalog-api env > env-vars.txt
   ```

3. Abra issue no GitHub com os arquivos anexados
