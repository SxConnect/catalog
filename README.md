# 🐾 SixPet Catalog Engine

Sistema completo de processamento e catalogação de produtos a partir de PDFs usando IA, com interface web moderna.

[![Build Backend](https://github.com/SxConnect/catalog/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/SxConnect/catalog/actions/workflows/docker-publish.yml)
[![Build Frontend](https://github.com/SxConnect/catalog/actions/workflows/docker-publish-frontend.yml/badge.svg)](https://github.com/SxConnect/catalog/actions/workflows/docker-publish-frontend.yml)

## 📁 Estrutura do Projeto

```
├── catalog/                    # Backend API (FastAPI + Python)
│   ├── app/                   # Código da aplicação
│   ├── alembic/               # Migrações do banco
│   ├── tests/                 # Testes automatizados
│   └── Dockerfile             # Build do backend
│
├── catalog-frontend/          # Frontend (Next.js + TypeScript)
│   ├── src/                   # Código da aplicação
│   │   ├── app/              # Pages e API routes
│   │   └── components/       # Componentes React
│   └── Dockerfile            # Build do frontend
│
├── .github/workflows/         # CI/CD GitHub Actions
├── docker-compose.prod.yml    # Deploy em produção
└── deploy.sh / deploy.ps1     # Scripts de deploy
```

## ✨ Características

### Backend (catalog/)
- 📄 Extração de dados de catálogos em PDF
- 🤖 Estruturação inteligente com IA (Groq)
- 🔍 Deduplicação automática de produtos
- 🌐 Enriquecimento de dados via web scraping
- 📦 Suporte a múltiplos formatos de storage (Filesystem, MinIO, S3)
- 🔄 Processamento assíncrono com Celery
- 🔑 Sistema de rotação de API keys
- 📊 API REST completa com FastAPI
- 🗄️ Banco otimizado para 1M+ produtos

### Frontend (catalog-frontend/)
- 🔐 Autenticação com NextAuth
- 🌓 Tema dark/light com persistência
- 📤 Upload de PDF com drag & drop
- 🎯 Seleção de campos para enriquecimento
- 📈 Dashboard com estatísticas
- 🔑 Gerenciamento de API Keys com visualização de uso
- ⚙️ Configurações de web scraping e processamento
- 📱 Interface responsiva e moderna

## 🚀 Deploy Rápido (Produção)

### 1. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.prod.example .env

# Editar variáveis (PostgreSQL, MinIO, Groq API, etc.)
nano .env
```

### 2. Executar Deploy
```bash
# Linux/Mac
./deploy.sh

# Windows PowerShell
./deploy.ps1
```

### 3. Acessar Sistema
- **Frontend**: https://catalog.sxconnect.com.br
- **Backend API**: https://catalog-api.sxconnect.com.br
- **Documentação**: https://catalog-api.sxconnect.com.br/docs

## 💻 Desenvolvimento Local

### Backend
```bash
cd catalog
docker-compose up -d
docker exec sixpet-catalog-api alembic upgrade head
```

### Frontend
```bash
cd catalog-frontend
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
- **Registry**: GitHub Container Registry (GHCR)
- **Proxy**: Traefik
- **SSL**: Let's Encrypt

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

## 🛠️ Comandos Úteis

```bash
# Ver logs
docker logs -f sixpet-catalog-frontend
docker logs -f sixpet-catalog-api

# Reiniciar serviços
docker restart sixpet-catalog-frontend
docker restart sixpet-catalog-api

# Executar migrations
docker exec sixpet-catalog-api alembic upgrade head

# Acessar banco
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# Parar tudo
docker-compose -f docker-compose.prod.yml down
```

## 🔄 CI/CD

O projeto usa GitHub Actions para build automático:

- **Push para main**: Gera imagens Docker versionadas
- **Tags**: Cria releases com versionamento semântico
- **GHCR**: Imagens publicadas no GitHub Container Registry

### Imagens Disponíveis
- `ghcr.io/sxconnect/catalog-backend:latest`
- `ghcr.io/sxconnect/catalog-frontend:latest`

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

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📞 Suporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/SxConnect/catalog/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/SxConnect/catalog/discussions)
- 📖 **Documentação**: Veja os arquivos específicos em cada pasta

---

**Desenvolvido com ❤️ para SixPet**