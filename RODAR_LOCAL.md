# 🚀 Como Rodar Localmente (Desenvolvimento)

## Por que rodar local?
- Testar se o código está funcionando
- Identificar se o problema é código ou infraestrutura
- Desenvolver novas features
- Debug mais fácil

## Pré-requisitos
- Docker Desktop instalado e rodando
- Node.js 18+ instalado
- Git

## Passo a Passo

### 1️⃣ Abrir 2 Terminais

**Terminal 1:** Backend (API)
**Terminal 2:** Frontend (Next.js)

### 2️⃣ Terminal 1 - Backend

```powershell
cd H:\dev-catalog\catalog
.\start-dev.ps1
```

Aguarde até ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Testar:** Abra http://localhost:8000/health no navegador
Deve mostrar: `{"status":"healthy"}`

### 3️⃣ Terminal 2 - Frontend

```powershell
cd H:\dev-catalog\catalog
.\start-frontend.ps1
```

Aguarde até ver:
```
✓ Ready in 3.5s
○ Local: http://localhost:3000
```

### 4️⃣ Acessar o Sistema

Abra: http://localhost:3000

**Login:**
- Email: `admin@sixpet.com`
- Senha: `admin123`

### 5️⃣ Testar Funcionalidades

- [ ] Dashboard carrega
- [ ] Upload de catálogo
- [ ] Produtos (lista, busca, filtros)
- [ ] API Keys (adicionar, remover)
- [ ] Settings (salvar configurações)
- [ ] Console sem erros de CORS

## Se der erro

### Backend não sobe

```powershell
# Ver logs
docker-compose logs api

# Verificar se PostgreSQL está rodando
docker-compose ps

# Recriar containers
docker-compose down
docker-compose up -d postgres redis minio
Start-Sleep -Seconds 10
docker-compose up api
```

### Frontend não conecta

1. Verificar se `frontend/.env.local` existe
2. Verificar se `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Verificar se backend está rodando (http://localhost:8000/health)

### Erro de CORS

Verificar em `app/main.py` se tem:
```python
allow_origins=[
    "http://localhost:3000",  # <-- DEVE TER ISSO
    ...
]
```

## Parar os Serviços

**Backend:**
```powershell
docker-compose down
```

**Frontend:**
Pressionar `Ctrl+C` no terminal

## Próximos Passos

Se funcionar local:
1. ✅ Código está correto
2. ❌ Problema é na infraestrutura de produção (Portainer/Traefik)
3. 🔍 Investigar logs do Portainer
4. 🔍 Verificar se containers estão rodando
5. 🔍 Verificar se Traefik está roteando corretamente

Se NÃO funcionar local:
1. ❌ Problema no código
2. 🐛 Debug e correção necessária
3. 📝 Enviar logs para análise
