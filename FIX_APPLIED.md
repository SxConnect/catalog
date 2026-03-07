# ✅ Correção Aplicada - Endpoint MinIO

## 🐛 Problema

```
ValueError: Invalid endpoint: minio-s3.sxconnect.com.br
```

O boto3 (cliente S3) precisa do protocolo `https://` no endpoint.

## ✅ Solução Aplicada

Atualizado `docker-compose.prod.yml`:

```yaml
# ANTES (errado)
- S3_ENDPOINT=${MINIO_S3_DOMAIN}

# DEPOIS (correto)
- S3_ENDPOINT=https://${MINIO_S3_DOMAIN}
- S3_REGION=us-east-1
```

## 🔄 Como Atualizar no Portainer

### Opção 1: Pull & Redeploy (Recomendado)

1. Acesse Portainer > Stacks > `catalog`
2. Clique em **Editor**
3. Clique em **Pull and redeploy**
4. Aguarde o pull da nova imagem
5. Clique em **Update the stack**

### Opção 2: Editar Manualmente

1. Acesse Portainer > Stacks > `catalog`
2. Clique em **Editor**
3. Localize as linhas:
   ```yaml
   - S3_ENDPOINT=${MINIO_S3_DOMAIN:-http://minio:9000}
   ```
4. Substitua por:
   ```yaml
   - S3_ENDPOINT=https://${MINIO_S3_DOMAIN:-minio-s3.sxconnect.com.br}
   - S3_REGION=us-east-1
   ```
5. Faça o mesmo para `api` e `worker`
6. Clique em **Update the stack**

### Opção 3: Recriar Stack

1. Portainer > Stacks > `catalog` > **Delete**
2. Stacks > **Add Stack**
3. Nome: `catalog`
4. Upload novo `docker-compose.prod.yml` do GitHub
5. Environment variables:
   ```env
   POSTGRES_USER=sixpet
   POSTGRES_PASSWORD=SuaSenha123!
   POSTGRES_DB=sixpet_catalog
   MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
   MINIO_ROOT_USER=admin
   MINIO_ROOT_PASSWORD=i7uDSxH$smwp
   S3_BUCKET=sixpet-catalog
   GROQ_API_KEYS=gsk_sua_key
   ```
6. Deploy

## ✅ Verificar

Após atualizar, verifique os logs:

```bash
docker logs sixpet-catalog-api -f
```

Deve aparecer:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Sem erros de `ValueError: Invalid endpoint`

## 🧪 Testar

```bash
# Health check
curl https://catalog-api.sxconnect.com.br/health

# Deve retornar
{"status":"healthy"}
```

## 📝 Variáveis Corretas

Certifique-se que no Portainer você tem:

```env
MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=i7uDSxH$smwp
S3_BUCKET=sixpet-catalog
```

O sistema automaticamente adiciona `https://` na frente.

## 🎯 Pronto!

Após aplicar a correção, o sistema deve iniciar sem erros e conectar ao MinIO corretamente.
