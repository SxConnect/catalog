# 🚀 RODAR LOCALHOST AGORA - Passo a Passo

## Status Atual
✅ PostgreSQL rodando (porta 5434)
✅ Redis rodando (porta 6381)
✅ MinIO rodando (portas 9000-9001)
✅ Frontend configurado (.env.local criado)
⏳ Backend fazendo build (pode demorar 5-10 minutos na primeira vez)

## Abrir 2 Terminais PowerShell

### Terminal 1 - Backend

```powershell
cd H:\dev-catalog\catalog
docker compose up api
```

**Aguarde até ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Testar:** Abra http://localhost:8000/health
Deve mostrar: `{"status":"healthy"}`

### Terminal 2 - Frontend

```powershell
cd H:\dev-catalog\catalog\frontend
npm run dev
```

**Aguarde até ver:**
```
✓ Ready in 3.5s
○ Local: http://localhost:3000
```

## Acessar o Sistema

Abra: **http://localhost:3000**

**Login:**
- Email: `admin@sixpet.com`
- Senha: `admin123`

## Testar Funcionalidades

Abra o Console do navegador (F12) e teste:

- [ ] Dashboard carrega sem erros
- [ ] Upload de catálogo
- [ ] Produtos (lista, busca, filtros)
- [ ] API Keys (adicionar, remover)
- [ ] Settings (salvar configurações)
- [ ] **Console SEM erros de CORS**
- [ ] **Console SEM erros 404**
- [ ] **Console SEM erros net::ERR_FAILED**

## Se Backend Demorar Muito

O primeiro build pode demorar 5-10 minutos porque precisa:
- Baixar imagem Python
- Instalar Tesseract OCR
- Instalar dependências Python

**Verificar progresso:**
```powershell
docker compose logs api --tail 50
```

## Se der Erro

### Backend não sobe

```powershell
# Ver logs completos
docker compose logs api

# Reconstruir do zero
docker compose down
docker compose build --no-cache api
docker compose up api
```

### Frontend não conecta

1. Verificar se `frontend/.env.local` tem:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

2. Verificar se backend está rodando:
   ```powershell
   curl http://localhost:8000/health
   ```

### Porta em uso

Se der erro "port already allocated":

```powershell
# Ver o que está usando a porta
netstat -ano | findstr :8000

# Parar o processo (substitua PID pelo número que apareceu)
taskkill /PID <PID> /F
```

## Parar Tudo

```powershell
# Parar backend (Ctrl+C no terminal 1)
# Parar frontend (Ctrl+C no terminal 2)

# Parar containers
docker compose down
```

## Próximos Passos

**Se funcionar local:**
- ✅ Código está 100% correto
- ❌ Problema é na infraestrutura de produção
- 🔍 Precisamos investigar Portainer/Traefik

**Se NÃO funcionar local:**
- Me envie os erros do console (F12)
- Me envie os logs: `docker compose logs api --tail 100`
