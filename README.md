# 🐾 SixPet Catalog Engine

Sistema completo de processamento e catalogação de produtos a partir de PDFs usando IA, com interface web moderna.

## ✨ Características

### Backend
- 📄 Extração de dados de catálogos em PDF
- 🤖 Estruturação inteligente com IA (Groq)
- 🔍 Deduplicação automática de produtos
- 🌐 Enriquecimento de dados via web scraping
- 📦 Suporte a múltiplos formatos de storage (Filesystem, MinIO, S3)
- 🔄 Processamento assíncrono com Celery
- 🔑 Sistema de rotação de API keys
- 📊 API REST completa com FastAPI
- 🗄️ Banco otimizado para 1M+ produtos

### Frontend
- 🔐 Autenticação com NextAuth
- 🌓 Tema dark/light com persistência
- 📤 Upload de PDF com drag & drop
- 🎯 Seleção de campos para enriquecimento
- 📈 Dashboard com estatísticas
- 🔑 Gerenciamento de API Keys com visualização de uso
- ⚙️ Configurações de web scraping e processamento
- 📱 Interface responsiva e moderna

## 🚀 Quick Start

### 📖 Documentação

- **[PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)** - ⭐ COMECE AQUI! Guia rápido de deploy
- **[DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)** - Guia completo passo a passo
- **[GIT_COMMANDS.md](GIT_COMMANDS.md)** - Comandos Git para enviar código
- **[COMANDOS_RAPIDOS.md](COMANDOS_RAPIDOS.md)** - Comandos úteis para o dia a dia
- **[RESUMO_COMPLETO.md](RESUMO_COMPLETO.md)** - Visão geral do projeto

### 🎯 Deploy em Produção (15 minutos)

```bash
# 1. Enviar código para GitHub
git add .
git commit -m "feat: add frontend application"
git push origin main

# 2. Gerar NEXTAUTH_SECRET
openssl rand -base64 32

# 3. Aguardar build no GitHub Actions
# https://github.com/SxConnect/catalog/actions

# 4. Configurar variáveis no Portainer e fazer deploy
# Veja PROXIMOS_PASSOS.md para detalhes
```

### 💻 Desenvolvimento Local

```bash
# Backend
docker-compose up -d
docker exec sixpet-catalog-api alembic upgrade head

# Frontend
cd frontend
npm install
npm run dev
```

## 🏗️ Tecnologias

### Backend
- **Framework**: FastAPI, Python 3.11
- **Banco de Dados**: PostgreSQL 15 com pg_trgm
- **Cache/Queue**: Redis 7
- **Worker**: Celery
- **IA**: Groq API (Llama 3)
- **OCR**: Tesseract, PyMuPDF, pdfplumber
- **Storage**: Filesystem, MinIO, AWS S3

### Frontend
- **Framework**: Next.js 14, React 18
- **Linguagem**: TypeScript
- **Estilo**: TailwindCSS
- **Autenticação**: NextAuth
- **State**: Zustand, React Query
- **Ícones**: Lucide React

### DevOps
- **Containers**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Registry**: GitHub Container Registry
- **Proxy**: Traefik
- **SSL**: Let's Encrypt

## 📁 Estrutura do Projeto

```
catalog/
├── frontend/              # Frontend Next.js
│   ├── src/
│   │   ├── app/          # Pages e API routes
│   │   ├── components/   # Componentes React
│   │   └── lib/          # Utilitários
│   └── Dockerfile
│
├── app/                   # Backend FastAPI
│   ├── api/              # Endpoints REST
│   ├── models/           # Modelos SQLAlchemy
│   ├── services/         # Lógica de negócio
│   └── tasks/            # Tarefas Celery
│
├── alembic/              # Migrations
├── .github/workflows/    # GitHub Actions
├── docker-compose.yml    # Desenvolvimento
├── docker-compose.prod.yml  # Produção
└── Documentação/
    ├── PROXIMOS_PASSOS.md
    ├── DEPLOY_GUIDE.md
    ├── COMANDOS_RAPIDOS.md
    └── RESUMO_COMPLETO.md
```

## 🌐 URLs de Produção

- **Frontend**: https://catalog.sxconnect.com.br
- **Backend API**: https://catalog-api.sxconnect.com.br
- **Documentação**: https://catalog-api.sxconnect.com.br/docs

## 🔧 Configuração

### Variáveis de Ambiente Principais

```bash
# PostgreSQL
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=sua_senha_forte
POSTGRES_DB=sixpet_catalog

# MinIO/S3
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=sua_senha_minio
S3_BUCKET=sixpet-catalog

# Groq API (separadas por vírgula)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# Frontend
NEXTAUTH_SECRET=gere_com_openssl_rand_base64_32
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=sua_senha_admin
```

Veja `.env.prod.example` para todas as variáveis.

## 📊 API Endpoints

### Catálogos

```bash
# Upload de catálogo
POST /api/catalogs/upload
Content-Type: multipart/form-data
X-API-Key: sua_chave

# Listar catálogos
GET /api/catalogs?page=1&page_size=20
X-API-Key: sua_chave
```

### Produtos

```bash
# Listar produtos
GET /api/products?page=1&page_size=20
X-API-Key: sua_chave

# Buscar produtos
GET /api/search?q=ração&category=pet
X-API-Key: sua_chave

# Obter produto
GET /api/products/{id}
X-API-Key: sua_chave
```

### Admin

```bash
# Configurações
GET /api/admin/settings
PUT /api/admin/settings

# API Keys
GET /api/admin/api-keys
POST /api/admin/api-keys
DELETE /api/admin/api-keys/{id}
```

## 🛠️ Comandos Úteis

```bash
# Ver logs
docker logs -f sixpet-catalog-frontend
docker logs -f sixpet-catalog-api

# Verificar deployment
bash check-deployment.sh

# Executar migrations
docker exec sixpet-catalog-api alembic upgrade head

# Acessar banco
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# Reiniciar serviços
docker restart sixpet-catalog-frontend
docker restart sixpet-catalog-api
```

Veja [COMANDOS_RAPIDOS.md](COMANDOS_RAPIDOS.md) para mais comandos.

## 🐛 Troubleshooting

Execute o script de verificação:

```bash
bash check-deployment.sh
```

Ou consulte:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problemas comuns
- [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) - Guia completo

## 📈 Performance

- ✅ Otimizado para 1M+ produtos
- ✅ Índices GIN e trigram no PostgreSQL
- ✅ Processamento assíncrono com Celery
- ✅ Cache com Redis
- ✅ Build otimizado (Next.js standalone)
- ✅ Multi-stage Docker build

## 🔐 Segurança

- ✅ Autenticação com NextAuth
- ✅ Senhas hasheadas (bcrypt)
- ✅ HTTPS obrigatório em produção
- ✅ Variáveis sensíveis em .env
- ✅ CORS configurado
- ✅ SQL injection protection

## 📝 Licença

MIT

## 🤝 Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## 📞 Suporte

- 📖 Documentação: Veja os arquivos .md na raiz
- 🐛 Issues: https://github.com/SxConnect/catalog/issues
- 💬 Discussões: https://github.com/SxConnect/catalog/discussions

---

**Desenvolvido com ❤️ para SixPet**
