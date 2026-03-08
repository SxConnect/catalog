# Rodar em Desenvolvimento Local

## 1. Criar arquivo .env

Copie o `.env.example` e crie `.env`:

```bash
cp .env.example .env
```

Edite o `.env` e adicione suas chaves Groq:
```
GROQ_API_KEYS=sua_chave_aqui
```

## 2. Subir Backend

```bash
docker-compose up -d postgres redis minio
docker-compose up api
```

O backend vai rodar em: http://localhost:8000

## 3. Testar Backend

```bash
curl http://localhost:8000/health
```

Deve retornar: `{"status":"healthy"}`

## 4. Rodar Migrations

```bash
docker-compose exec api alembic upgrade head
```

## 5. Subir Frontend

Em outro terminal:

```bash
cd frontend
npm install
```

Crie `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=dev-secret-change-in-production
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=admin123
```

Rode o frontend:
```bash
npm run dev
```

Frontend vai rodar em: http://localhost:3000

## 6. Testar

1. Abrir http://localhost:3000
2. Fazer login com:
   - Email: admin@sixpet.com
   - Senha: admin123
3. Testar todas as páginas

## Troubleshooting

### Backend não sobe
```bash
docker-compose logs api
```

### Frontend não conecta
Verificar se `NEXT_PUBLIC_API_URL` está correto no `.env.local`

### Erro de CORS
Verificar se `http://localhost:3000` está em `allow_origins` no `app/main.py`
