# 🚀 Deploy Final - SixPet Catalog (Backend + Frontend)

## 📋 Pré-requisitos

- Servidor com Docker e Portainer
- Traefik configurado na rede `portainer_default`
- DNS configurado:
  - `catalog.sxconnect.com.br` → IP do servidor
  - `catalog-api.sxconnect.com.br` → IP do servidor
- MinIO rodando em `mins3.sxconnect.com.br`
- Bucket `sixpet-catalog` criado no MinIO

## ⚡ Deploy em 3 Passos

### 1. Gerar Secrets

```bash
# NEXTAUTH_SECRET
openssl rand -base64 32

# Copie o resultado, você vai precisar
```

### 2. Configurar Variáveis no Portainer

No Portainer, ao criar/editar o stack, adicione estas variáveis:

```bash
# PostgreSQL
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gkGSIXJ157Dbf

# MinIO
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=lkasdl1fdkasmdk231eowd290dwop33
S3_BUCKET=sixpet-catalog

# Groq API Keys (separadas por vírgula)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# Frontend - NextAuth (cole o secret gerado no passo 1)
NEXTAUTH_SECRET=cole_aqui_o_secret_gerado

# Frontend - Admin (PERSONALIZE!)
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=SuaSenhaForte123!
```

### 3. Deploy no Portainer

#### Opção A: Atualizar Stack Existente

1. Vá em **Stacks** → Selecione `catalog`
2. Clique em **Editor**
3. O docker-compose.prod.yml já está atualizado com o frontend
4. Adicione as novas variáveis de ambiente (NEXTAUTH_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD)
5. Clique em **Update the stack**

#### Opção B: Criar Novo Stack

1. **Stacks** → **Add Stack**
2. Nome: `catalog`
3. Build method: **Repository**
4. Repository URL: `https://github.com/SxConnect/catalog`
5. Repository reference: `refs/heads/main`
6. Compose path: `docker-compose.prod.yml`
7. Environment variables: (cole as variáveis do passo 2)
8. **Deploy the stack**

## 🔄 Aguardar Build

O GitHub Actions vai construir as imagens automaticamente:

1. **Backend**: `ghcr.io/sxconnect/catalog:latest` (~3 min)
2. **Frontend**: `ghcr.io/sxconnect/catalog-frontend:latest` (~3 min)

Acompanhe em: https://github.com/SxConnect/catalog/actions

## ✅ Verificar Deploy

```bash
# Ver containers
docker ps | grep sixpet-catalog

# Deve mostrar 5 containers:
# - sixpet-catalog-postgres (healthy)
# - sixpet-catalog-redis (healthy)
# - sixpet-catalog-api (healthy)
# - sixpet-catalog-worker (running)
# - sixpet-catalog-frontend (healthy)

# Ver logs
docker logs -f sixpet-catalog-frontend
docker logs -f sixpet-catalog-api

# Testar endpoints
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health
```

## 🎯 Executar Migrations

Após o deploy, execute as migrations:

```bash
# Migration 001 (tabelas principais)
docker exec sixpet-catalog-api alembic upgrade head

# Verificar tabelas criadas
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "\dt"

# Deve mostrar:
# - ai_api_keys
# - alembic_version
# - catalogs
# - products_catalog
# - settings
```

## 🌐 Acessar Sistema

### Frontend
https://catalog.sxconnect.com.br

Login com as credenciais configuradas no .env:
- Email: `admin@sixpet.com` (ou o que você configurou)
- Senha: A que você configurou em `ADMIN_PASSWORD`

### Backend API
https://catalog-api.sxconnect.com.br/docs

## 📊 Estrutura Final

```
┌─────────────────────────────────────┐
│   Traefik (Proxy + SSL)             │
│   - catalog.sxconnect.com.br        │
│   - catalog-api.sxconnect.com.br    │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┬──────────────┐
    │             │              │
┌───▼────┐   ┌───▼────┐    ┌───▼────┐
│Frontend│   │  API   │    │ Worker │
│ :3000  │   │ :8000  │    │ Celery │
└────────┘   └───┬────┘    └───┬────┘
                 │              │
         ┌───────┴──────┬───────┴────┐
         │              │            │
     ┌───▼───┐     ┌───▼───┐   ┌───▼────┐
     │ PG    │     │ Redis │   │ MinIO  │
     │ :5432 │     │ :6379 │   │ Externo│
     └───────┘     └───────┘   └────────┘
```

## 🔧 Configurações Iniciais

Após fazer login no frontend:

### 1. Configurar API Keys Groq
- Vá em **API Keys**
- Adicione suas chaves Groq
- Monitore o uso em tempo real

### 2. Configurar Web Scraping
- Vá em **Configurações** → **Web Scraping**
- Defina extrações por segundo
- Configure URL base (se usar)
- Habilite/desabilite conforme necessário

### 3. Fazer Upload de Teste
- Vá em **Upload**
- Arraste um PDF de catálogo
- Marque os campos para enriquecimento
- Envie e acompanhe o processamento

## 🐛 Troubleshooting

### Frontend não carrega

```bash
# Verificar logs
docker logs sixpet-catalog-frontend

# Verificar se API está acessível
curl https://catalog-api.sxconnect.com.br/health

# Reiniciar
docker restart sixpet-catalog-frontend
```

### Erro de autenticação no login

```bash
# Verificar variáveis
docker exec sixpet-catalog-frontend env | grep -E "ADMIN|NEXTAUTH"

# Recriar container com novas variáveis
docker-compose -f docker-compose.prod.yml up -d frontend
```

### API não responde

```bash
# Verificar PostgreSQL
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT 1;"

# Verificar migrations
docker exec sixpet-catalog-api alembic current

# Reiniciar API
docker restart sixpet-catalog-api
```

### Tema dark/light não funciona

- Limpar cache do navegador
- Verificar se JavaScript está habilitado
- Testar em modo anônimo

## 🔄 Atualizar Sistema

```bash
# Puxar novas imagens
docker pull ghcr.io/sxconnect/catalog:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Recriar containers
docker-compose -f docker-compose.prod.yml up -d

# Ou via Portainer: Update the stack
```

## 📝 Variáveis de Ambiente Completas

```bash
# PostgreSQL
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gkGSIXJ157Dbf
POSTGRES_DB=sixpet_catalog

# MinIO
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=lkasdl1fdkasmdk231eowd290dwop33
S3_BUCKET=sixpet-catalog

# Groq
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# Frontend
NEXTAUTH_SECRET=seu_secret_gerado_com_openssl
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=SuaSenhaForte123!
```

## ✅ Checklist Final

- [ ] DNS configurado
- [ ] Bucket MinIO criado
- [ ] NEXTAUTH_SECRET gerado
- [ ] Variáveis configuradas no Portainer
- [ ] Stack deployed
- [ ] GitHub Actions executou com sucesso
- [ ] Migrations executadas
- [ ] Frontend acessível
- [ ] Backend acessível
- [ ] Login funcionando
- [ ] Tema dark/light funcionando
- [ ] Upload de PDF funcionando
- [ ] API Keys configuradas

---

**Status**: ✅ Sistema completo pronto para produção!
**URLs**:
- Frontend: https://catalog.sxconnect.com.br
- Backend: https://catalog-api.sxconnect.com.br
