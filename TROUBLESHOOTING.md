# 🔧 Troubleshooting - SixPet Catalog

## ❌ Erro: password authentication failed for user

```
FATAL: password authentication failed for user "sixpet_catalog_user"
```

### Causa
As variáveis de ambiente do PostgreSQL não estão corretas.

### Solução

No Portainer, verifique as variáveis de ambiente:

```env
# ❌ ERRADO
POSTGRES_USER=sixpet_catalog_user

# ✅ CORRETO
POSTGRES_USER=sixpet
```

**Variáveis corretas:**
```env
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gKoJrI57Duf
POSTGRES_DB=sixpet_catalog
```

### Como Corrigir

1. Portainer > Stacks > catalog > **Editor**
2. Scroll até **Environment variables**
3. Corrigir:
   - `POSTGRES_USER` → `sixpet`
   - `POSTGRES_DB` → `sixpet_catalog`
4. **Update the stack**

---

## ❌ Erro: Invalid endpoint MinIO

```
ValueError: Invalid endpoint: minio-s3.sxconnect.com.br
```

### Causa
Endpoint sem protocolo `https://`

### Solução

Aguarde o build da nova imagem no GitHub Actions (já corrigido no código).

Ou adicione manualmente no `.env`:
```env
S3_ENDPOINT=https://minio-s3.sxconnect.com.br
```

---

## ❌ Container não inicia

### Verificar logs
```bash
-catalog-api -f
docker logs sixpet-catalog-worker -f
docker logs sixpet-catalog-postgres -f
```

### Verificar variáveis
```bash
docker exec sixpet-catalog-api env | grep -E "DATABASE|MINIO|S3"
```

---

## ❌ PostgreSQL não conecta

### Verificar se está rodando
```bash
docker ps | grep postgres
docker exec sixpet-catalog-postgres pg_isready -U sixpet
```

### Testar conexão
```bash
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT 1"
```

### Recriar banco (se necessário)
```bash
# Parar stack
docker-compose -f docker-compose.prod.yml down

# Remover volume
docker volume rm catalog_postgres_data

# Subir novamente
docker-compose -f docker-compose.prod.yml up -d
```

---

## ❌ MinIO não conecta

### Verificar credenciais
```bash
# Testar com mc
mc alias set test https://minio-s3.sxconnect.com.br admin i7uDSxH$smwp
mc ls test/
```

### Verificar bucket
```bash
mc ls test/sixpet-catalog
# Se não existir, criar:
mc mb test/sixpet-catalog
mc anonymous set download test/sixpet-catalog
```

---

## ❌ Worker não processa

### Verificar Redis
```bash
docker exec sixpet-catalog-redis redis-cli ping
# Deve retornar: PONG
```

### Ver fila
```bash
docker exec sixpet-catalog-redis redis-cli LLEN celery
```

### Restart worker
```bash
docker restart sixpet-catalog-worker
docker logs sixpet-catalog-worker -f
```

---

## ❌ API retorna 500

### Ver logs detalhados
```bash
docker logs sixpet-catalog-api -f --tail 100
```

### Testar health
```bash
curl https://catalog-api.sxconnect.com.br/health
```

### Entrar no container
```bash
docker exec -it sixpet-catalog-api bash

# Testar imports
python -c "from app.main import app; print('OK')"

# Testar DB
python -c "from app.database import engine; print(engine.url)"
```

---

## ✅ Checklist de Variáveis

Certifique-se que tem TODAS estas variáveis no Portainer:

```env
# PostgreSQL
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gKoJrI57Duf
POSTGRES_DB=sixpet_catalog

# MinIO
MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=i7uDSxH$smwp
3_BUCKET=sixpet-catalog

# Groq
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3
```

---

## 🔄 Restart Completo

Se nada funcionar, restart completo:

```bash
# Parar tudo
docker-compose -f docker-compose.prod.yml down

# Limpar (CUIDADO: apaga dados!)
docker volume rm catalog_postgres_data

# Subir novamente
docker-compose -f docker-compose.prod.yml up -d

# Aguardar containers ficarem healthy
docker ps

# Ver logs
docker logs sixpet-catalog-api -f
```

---

## 📞 Suporte

Se o problema persistir:

docker logs sixpet-catalog-api > logs.txt`
2. Abra issue: https://github.com/SxConnect/catalog/issues
3. Cole os logs e descreva o problema
1. Copie os logs: `