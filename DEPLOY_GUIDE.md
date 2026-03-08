# 🚀 Guia de Deploy Completo - SixPet Catalog

## 📦 Passo 1: Enviar Código para GitHub

O código do frontend já foi copiado para `catalog/frontend/`. Agora precisa fazer commit e push:

```bash
cd catalog

# Verificar status
git status

# Adicionar todos os arquivos
git add .

# Commit
git commit -m "feat: add frontend application with Next.js 14"

# Push para GitHub
git push origin main
```

## ⏳ Passo 2: Aguardar Build no GitHub Actions

Após o push, o GitHub Actions vai construir automaticamente as imagens Docker:

1. Acesse: https://github.com/SxConnect/catalog/actions
2. Aguarde os workflows completarem (~5-7 minutos):
   - ✅ **Build and Push Docker Image** (backend)
   - ✅ **Build and Push Frontend Docker Image** (frontend)

As imagens serão publicadas em:
- `ghcr.io/sxconnect/catalog:latest`
- `ghcr.io/sxconnect/catalog-frontend:latest`

## 🔐 Passo 3: Gerar NEXTAUTH_SECRET

```bash
openssl rand -base64 32
```

Copie o resultado, você vai precisar no próximo passo.

## ⚙️ Passo 4: Configurar Variáveis no Portainer

No Portainer, ao criar/editar o stack `catalog`, adicione estas variáveis de ambiente:

```bash
# PostgreSQL
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gkGSIXJ157Dbf
POSTGRES_DB=sixpet_catalog

# MinIO (usar o existente)
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=lkasdl1fdkasmdk231eowd290dwop33
S3_BUCKET=sixpet-catalog

# Groq API Keys (separadas por vírgula)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# Frontend - NextAuth (cole o secret gerado no passo 3)
NEXTAUTH_SECRET=cole_aqui_o_secret_gerado_no_passo_3

# Frontend - Admin (PERSONALIZE!)
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=SuaSenhaForte123!
```

## 🐳 Passo 5: Deploy no Portainer

### Opção A: Atualizar Stack Existente

1. Acesse Portainer
2. Vá em **Stacks** → Selecione `catalog`
3. Clique em **Editor**
4. O `docker-compose.prod.yml` já está atualizado com o serviço frontend
5. Adicione as novas variáveis de ambiente (NEXTAUTH_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD)
6. Clique em **Update the stack**
7. Aguarde os containers subirem

### Opção B: Criar Novo Stack

1. **Stacks** → **Add Stack**
2. Nome: `catalog`
3. Build method: **Repository**
4. Repository URL: `https://github.com/SxConnect/catalog`
5. Repository reference: `refs/heads/main`
6. Compose path: `docker-compose.prod.yml`
7. Environment variables: (cole as variáveis do passo 4)
8. **Deploy the stack**

## ✅ Passo 6: Verificar Containers

```bash
# Ver todos os containers
docker ps | grep sixpet-catalog

# Deve mostrar 5 containers rodando:
# ✅ sixpet-catalog-postgres (healthy)
# ✅ sixpet-catalog-redis (healthy)
# ✅ sixpet-catalog-api (healthy)
# ✅ sixpet-catalog-worker (running)
# ✅ sixpet-catalog-frontend (healthy)
```

## 🗄️ Passo 7: Executar Migrations

```bash
# Executar migrations
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

## 🧪 Passo 8: Testar Endpoints

```bash
# Testar backend
curl https://catalog-api.sxconnect.com.br/health
# Deve retornar: {"status":"healthy"}

# Testar frontend
curl https://catalog.sxconnect.com.br/api/health
# Deve retornar: {"status":"ok"}
```

## 🌐 Passo 9: Acessar Sistema

### Frontend
**URL**: https://catalog.sxconnect.com.br

**Login**:
- Email: O que você configurou em `ADMIN_EMAIL`
- Senha: O que você configurou em `ADMIN_PASSWORD`

### Backend API
**URL**: https://catalog-api.sxconnect.com.br/docs

Documentação interativa Swagger UI

## 🎯 Passo 10: Configuração Inicial

Após fazer login no frontend:

### 1. Adicionar API Keys Groq
- Vá em **API Keys** (menu lateral)
- Clique em **Adicionar Nova Chave**
- Cole sua chave Groq (começa com `gsk_`)
- Salve
- Repita para adicionar mais chaves (recomendado: 3-5 chaves para rotação)

### 2. Configurar Web Scraping
- Vá em **Configurações** → aba **Web Scraping**
- Defina **Extrações por segundo**: 10-50 (recomendado: 20)
- Configure **URL base** se necessário
- Habilite/desabilite conforme necessário
- Clique em **Salvar Configurações**

### 3. Configurar Processamento
- Vá em **Configurações** → aba **Processamento**
- **Catálogos simultâneos**: 2-4 (recomendado: 2)
- **Deduplicação**: Habilitado
- **Threshold de similaridade**: 0.8 (80%)
- Clique em **Salvar Configurações**

### 4. Fazer Upload de Teste
- Vá em **Upload**
- Arraste um PDF de catálogo ou clique para selecionar
- Marque os campos que deseja enriquecer:
  - ✅ Nome (obrigatório)
  - ✅ Marca (obrigatório)
  - ✅ EAN (obrigatório)
  - ✅ Categoria
  - ✅ Descrição
  - ✅ Preço
  - ✅ Peso
  - ✅ Dimensões
  - ✅ Ingredientes
  - ✅ Informações Nutricionais
  - ✅ Imagens
  - ✅ Estoque
- Clique em **Enviar Catálogo**
- Acompanhe o processamento no Dashboard

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
│Next.js │   │FastAPI │    │        │
└────────┘   └───┬────┘    └───┬────┘
                 │              │
         ┌───────┴──────┬───────┴────┐
         │              │            │
     ┌───▼───┐     ┌───▼───┐   ┌───▼────┐
     │ PG    │     │ Redis │   │ MinIO  │
     │ :5432 │     │ :6379 │   │ Externo│
     └───────┘     └───────┘   └────────┘
```

## 🐛 Troubleshooting

### Frontend não carrega

```bash
# Ver logs
docker logs -f sixpet-catalog-frontend

# Verificar se API está acessível
curl https://catalog-api.sxconnect.com.br/health

# Reiniciar
docker restart sixpet-catalog-frontend
```

### Erro de autenticação no login

```bash
# Verificar variáveis
docker exec sixpet-catalog-frontend env | grep -E "ADMIN|NEXTAUTH"

# Se estiver errado, atualizar no Portainer e recriar
docker-compose -f docker-compose.prod.yml up -d frontend
```

### API não responde

```bash
# Verificar PostgreSQL
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT 1;"

# Verificar migrations
docker exec sixpet-catalog-api alembic current

# Ver logs
docker logs -f sixpet-catalog-api

# Reiniciar
docker restart sixpet-catalog-api
```

### Worker não processa

```bash
# Ver logs
docker logs -f sixpet-catalog-worker

# Verificar Redis
docker exec sixpet-catalog-redis redis-cli ping

# Reiniciar
docker restart sixpet-catalog-worker
```

### Tema dark/light não funciona

- Limpar cache do navegador (Ctrl+Shift+Delete)
- Verificar se JavaScript está habilitado
- Testar em modo anônimo
- Verificar console do navegador (F12) para erros

## 🔄 Atualizar Sistema

Quando houver novas versões:

```bash
# No servidor
docker pull ghcr.io/sxconnect/catalog:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Recriar containers
docker-compose -f docker-compose.prod.yml up -d

# Ou via Portainer: Update the stack
```

## 📝 Checklist Final

- [ ] Código commitado e enviado para GitHub
- [ ] GitHub Actions executou com sucesso (ambos workflows)
- [ ] NEXTAUTH_SECRET gerado
- [ ] Variáveis configuradas no Portainer
- [ ] Stack deployed no Portainer
- [ ] 5 containers rodando (postgres, redis, api, worker, frontend)
- [ ] Migrations executadas
- [ ] Backend acessível (https://catalog-api.sxconnect.com.br/health)
- [ ] Frontend acessível (https://catalog.sxconnect.com.br)
- [ ] Login funcionando
- [ ] Tema dark/light funcionando
- [ ] API Keys adicionadas
- [ ] Configurações ajustadas
- [ ] Upload de PDF testado

## 🎉 Pronto!

Sistema completo em produção!

**URLs**:
- 🌐 Frontend: https://catalog.sxconnect.com.br
- 🔌 Backend API: https://catalog-api.sxconnect.com.br
- 📚 Documentação: https://catalog-api.sxconnect.com.br/docs

**Próximos Passos**:
1. Fazer upload dos catálogos em PDF
2. Monitorar processamento no Dashboard
3. Verificar produtos extraídos
4. Ajustar configurações conforme necessário
5. Adicionar mais API Keys Groq se necessário
