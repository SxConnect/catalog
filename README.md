# SixPet Catalog Engine

Sistema automatizado de processamento de catálogos PDF para construir banco de dados de produtos do mercado pet brasileiro.

## 🚀 Funcionalidades

- Upload e processamento de catálogos PDF
- Extração automática de imagens e texto (OCR)
- Estruturação de dados com IA (Groq)
- Detecção de duplicatas (pg_trgm + EAN único)
- Storage configurável (Filesystem, MinIO, S3)
- Processamento paralelo com Celery
- Busca full-text otimizada (GIN indexes)
- API REST completa

## 🏗️ Arquitetura

```
FastAPI + PostgreSQL + Redis + Celery + Docker
```

### Stack Tecnológica

- **Backend:** Python 3.11, FastAPI
- **Banco:** PostgreSQL 15 (pg_trgm, full-text search)
- **Cache/Queue:** Redis + Celery
- **PDF:** PyMuPDF, pdfplumber, Tesseract OCR
- **IA:** Groq API (estruturação de dados)
- **Storage:** Filesystem / MinIO / AWS S3
- **Deploy:** Docker Compose

## 📦 Instalação

### Pré-requisitos

- Docker & Docker Compose
- Groq API Keys (para IA)

### Quick Start

```bash
# 1. Clone o repositório
git clone <repo-url>
cd catalog

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Inicie os serviços
docker-compose up -d

# 4. Acesse a API
http://localhost:8000
http://localhost:8000/docs  # Swagger UI
```

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql://sixpet:sixpet123@postgres:5432/sixpet_catalog

# Redis
REDIS_URL=redis://redis:6379/0

# Groq API Keys (rotação automática)
GROQ_API_KEYS=gsk_key1,gsk_key2,gsk_key3

# Storage (filesystem, minio, s3)
STORAGE_TYPE=filesystem
STORAGE_PATH=/app/storage

# MinIO/S3 (opcional)
S3_ENDPOINT=http://minio:9000
S3_BUCKET=sixpet-catalog
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

## 📊 Modelo de Dados

### Produto

```json
{
  "id": 1,
  "ean": "7891234567890",
  "name": "Ração Premium para Cães Adultos",
  "brand": "Royal Canin",
  "category": "Alimentação",
  "description": "Ração completa e balanceada...",
  "images": ["/storage/products/images/abc123.png"],
  "attributes": {
    "weight": "15kg",
    "flavor": "Frango"
  },
  "source_catalog": "catalogo-2025.pdf",
  "confidence_score": 0.95,
  "created_at": "2026-03-07T10:00:00Z"
}
```

### Índices de Performance

- **EAN:** Índice único (detecção de duplicatas)
- **Nome/Marca:** Índices trigram GIN (busca fuzzy)
- **Full-text:** Índice GIN (busca em português)
- **Compostos:** name+brand+category

## 🔍 API Endpoints

### Upload de Catálogo

```bash
POST /api/catalog/upload
Content-Type: multipart/form-data

# Response
{
  "catalog_id": 123,
  "status": "processing"
}
```

### Buscar Produtos

```bash
# Busca full-text
GET /api/search/?q=ração+premium

# Busca por EAN
GET /api/search/by-ean/7891234567890

# Busca por marca
GET /api/search/by-brand/Royal%20Canin
```

### Verificar Duplicatas

```bash
GET /api/deduplication/check?name=Ração+Premium&brand=Royal+Canin&ean=7891234567890

# Response
{
  "is_duplicate": true,
  "duplicate_product": {
    "id": 123,
    "name": "Ração Premium para Cães",
    "ean": "7891234567890"
  }
}
```

### Exportar Dados

```bash
GET /api/products/export/json
GET /api/products/export/csv
```

## 🎯 Detecção de Duplicatas

O sistema usa **pg_trgm similarity** para detectar duplicatas:

1. **EAN exato** (prioridade máxima)
2. **Similaridade trigram** (nome + marca)
   - Score: `similarity(name) * 0.7 + similarity(brand) * 0.3`
   - Threshold: 0.85 (configurável)

### Comportamento

```python
# Catálogo 1: EAN 7891234567890
→ Cria produto novo

# Catálogo 2: MESMO EAN
→ Atualiza produto existente
→ Adiciona novas imagens
→ Aumenta confidence_score
→ NÃO cria duplicata ✅
```

## 📈 Performance

### Teste Real (122 páginas, 2,428 imagens)

- **Tempo:** 45 segundos (0.37s/página)
- **Memória:** ~300 MB por catálogo
- **Throughput:** ~162 páginas/minuto
- **Erros:** 0

### Escalabilidade

| Workers | Catálogos/hora | Memória Total |
|---------|----------------|---------------|
| 10      | ~800           | ~3 GB         |
| 50      | ~4,000         | ~15 GB        |

Suporta **1M+ produtos** com índices otimizados.

## 🗄️ Storage

### Opções Disponíveis

1. **Filesystem** (padrão) - Desenvolvimento
2. **MinIO** (recomendado) - Produção self-hosted
3. **AWS S3** - Cloud

Configure via `STORAGE_TYPE` no `.env`.

## 🔄 Fluxo de Processamento

```
1. Upload PDF → Salva no storage
2. Celery Task → Divide em páginas
3. Extrai imagens → Salva com hash único
4. Extrai texto → OCR se necessário
5. IA estrutura → JSON padronizado (Groq)
6. Verifica duplicatas → EAN + similaridade
7. Salva/Atualiza → PostgreSQL
8. Pronto para exportação
```

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
catalog/
├── app/
│   ├── api/              # Endpoints FastAPI
│   ├── models/           # SQLAlchemy models
│   ├── services/         # Lógica de negócio
│   ├── tasks/            # Celery tasks
│   └── utils/            # Utilitários
├── alembic/              # Migrations
├── storage/              # Armazenamento local
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Rodar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar migrations
alembic upgrade head

# Iniciar API
uvicorn app.main:app --reload

# Iniciar worker
celery -A app.tasks.worker worker --loglevel=info
```

## 📝 Licença

MIT

## 🤝 Contribuindo

Pull requests são bem-vindos!

## 📧 Contato

Para dúvidas ou suporte, abra uma issue no GitHub.
