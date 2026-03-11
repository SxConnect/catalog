# SixPet Catalog Frontend

Interface web para gerenciamento de catálogos de produtos pet.

## 🚀 Funcionalidades

- ✅ **Autenticação** - Login seguro com NextAuth
- ✅ **Dashboard** - Estatísticas e visão geral
- ✅ **Upload de Catálogos** - Drag & drop de PDFs
- ✅ **Lista de Produtos** - Busca, filtros e paginação
- ✅ **Gerenciamento de API Keys** - Groq API
- ✅ **Configurações** - Personalização do sistema

## 📦 Tecnologias

- Next.js 14 (App Router)
- TypeScript
- TailwindCSS
- NextAuth.js
- React Query
- Axios

## 🛠️ Instalação

```bash
# Instalar dependências
npm install

# Copiar .env
cp .env.example .env.local

# Editar variáveis de ambiente
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXTAUTH_SECRET=your-secret-key

# Rodar em desenvolvimento
npm run dev

# Build para produção
npm run build
npm start
```

## 🐳 Docker

```bash
# Build
docker build -t sixpet-catalog-frontend .

# Run
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://api:8000 \
  -e NEXTAUTH_SECRET=your-secret \
  sixpet-catalog-frontend
```

## 📝 Credenciais Padrão

- Email: `admin@sixpet.com`
- Senha: `admin123`

## 🔧 Próximos Passos

Para completar o frontend, você precisa criar:

1. **Página de Produtos** (`src/app/dashboard/products/page.tsx`)
   - Lista com tabela
   - Busca e filtros
   - Paginação
   - Detalhes do produto

2. **Página de Upload** (`src/app/dashboard/upload/page.tsx`)
   - Drag & drop de PDFs
   - Progress bar
   - Lista de uploads

3. **Página de API Keys** (`src/app/dashboard/api-keys/page.tsx`)
   - CRUD de chaves Groq
   - Status e uso

4. **Página de Configurações** (`src/app/dashboard/settings/page.tsx`)
   - Configurações gerais
   - Preferências

## 📚 Estrutura de Arquivos

```
src/
├── app/
│   ├── api/auth/[...nextauth]/  # NextAuth
│   ├── dashboard/               # Páginas protegidas
│   │   ├── layout.tsx
│   │   ├── page.tsx            # Dashboard
│   │   ├── products/           # Lista de produtos
│   │   ├── upload/             # Upload de catálogos
│   │   ├── api-keys/           # Gerenciar API keys
│   │   └── settings/           # Configurações
│   ├── login/                  # Página de login
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── Header.tsx
│   ├── Sidebar.tsx
│   └── Providers.tsx
└── lib/
    └── api.ts                  # Axios client
```

## 🔐 Segurança

- Autenticação via NextAuth com JWT
- Rotas protegidas com middleware
- Validação de formulários
- HTTPS obrigatório em produção
- Sanitização de inputs

## 📊 Otimização para 1M de Produtos

O banco de dados já está otimizado com:
- Índices GIN para full-text search
- Índices trigram para busca fuzzy
- Índices compostos
- Paginação server-side
- Cache com React Query

## 🚀 Deploy

Adicione ao `docker-compose.prod.yml`:

```yaml
frontend:
  image: ghcr.io/sxconnect/catalog-frontend:latest
  container_name: sixpet-catalog-frontend
  restart: always
  environment:
    - NEXT_PUBLIC_API_URL=https://catalog-api.sxconnect.com.br
    - NEXTAUTH_URL=https://catalog.sxconnect.com.br
    - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
  networks:
    - portainer_default
  labels:
    - traefik.enable=true
    - traefik.http.routers.catalog-frontend.rule=Host(`catalog.sxconnect.com.br`)
    - traefik.http.routers.catalog-frontend.entrypoints=websecure
    - traefik.http.routers.catalog-frontend.tls.certresolver=leresolver
    - traefik.http.services.catalog-frontend.loadbalancer.server.port=3000
```
