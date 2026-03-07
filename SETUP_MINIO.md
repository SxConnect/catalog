# Configurar MinIO Existente

Como você já tem o MinIO instalado, basta criar o bucket e configurar as variáveis.

## 1️⃣ Criar Bucket no MinIO

### Via Console Web

1. Acesse: https://minio.sxconnect.com.br
2. Login com suas credenciais
3. **Buckets** > **Create Bucket**
4. Nome: `sixpet-catalog`
5. **Access Policy:** Public (para imagens serem acessíveis)
6. Create

### Via CLI (mc)

```bash
# Configurar alias (se ainda não tiver)
mc alias set myminio https://minio-s3.sxconnect.com.br admin SUA_SENHA

# Criar bucket
mc mb myminio/sixpet-catalog

# Tornar público (para imagens)
mc anonymous set download myminio/sixpet-catalog
```

## 2️⃣ Configurar .env

No Portainer, ao criar a stack, adicione estas variáveis:

```env
# Database
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=SuaSenhaForte123!
POSTGRES_DB=sixpet_catalog

# MinIO Existente
MINIO_S3_DOMAIN=minio-s3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=i7uDSxH$smwp
S3_BUCKET=sixpet-catalog

# Groq API Keys
GROQ_API_KEYS=gsk_sua_key_1,gsk_sua_key_2
```

## 3️⃣ Deploy

O `docker-compose.prod.yml` já está configurado para usar o MinIO existente:

- ✅ Não cria novo container MinIO
- ✅ Usa `MINIO_S3_DOMAIN` para conectar
- ✅ Usa credenciais do MinIO existente
- ✅ Imagens serão salvas em `https://minio-s3.sxconnect.com.br/sixpet-catalog/`

## 4️⃣ Testar Conexão

Após deploy, teste se está funcionando:

```bash
# Entrar no container
docker exec -it sixpet-catalog-api bash

# Testar conexão MinIO
python -c "
import boto3
s3 = boto3.client(
    's3',
    endpoint_url='https://minio-s3.sxconnect.com.br',
    aws_access_key_id='admin',
    aws_secret_access_key='i7uDSxH\$smwp'
)
print(s3.list_buckets())
"
```

## 5️⃣ Verificar Imagens

Após processar um catálogo, as imagens estarão em:

```
https://minio-s3.sxconnect.com.br/sixpet-catalog/products/images/1/abc123.png
```

## ✅ Pronto!

O sistema usará o MinIO existente sem criar containers adicionais.

## 🔧 Troubleshooting

### Erro de conexão

```bash
# Verificar se MinIO está acessível
curl https://minio-s3.sxconnect.com.br

# Testar credenciais
mc alias set test https://minio-s3.sxconnect.com.br admin SUA_SENHA
mc ls test/
```

### Bucket não encontrado

```bash
# Listar buckets
mc ls myminio/

# Criar se não existir
mc mb myminio/sixpet-catalog
```

### Imagens não acessíveis

```bash
# Tornar bucket público
mc anonymous set download myminio/sixpet-catalog

# Verificar policy
mc anonymous get myminio/sixpet-catalog
```
