# 🚀 Rodar Backend SEM Docker (Mais Rápido)

O build do Docker está demorando muito. Vamos rodar o backend direto com Python.

## Pré-requisitos

- Python 3.11 instalado
- PostgreSQL rodando (já está via Docker)
- Redis rodando (já está via Docker)

## Passo a Passo

### 1. Criar ambiente virtual

```powershell
cd H:\dev-catalog\catalog
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```powershell
pip install -r requirements.txt
```

### 3. Configurar .env

Editar `H:\dev-catalog\catalog\.env` e mudar:

```env
DATABASE_URL=postgresql://sixpet:sixpet123@localhost:5434/sixpet_catalog
REDIS_URL=redis://localhost:6381/0
STORAGE_TYPE=filesystem
STORAGE_PATH=./storage
```

### 4. Rodar migrations

```powershell
alembic upgrade head
```

### 5. Iniciar backend

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Testar

Abrir: http://localhost:8000/health

Deve mostrar: `{"status":"healthy"}`

### 7. Recarregar frontend

Abrir: http://localhost:3000

Fazer login e testar tudo!

## Se der erro

### ModuleNotFoundError

```powershell
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Erro de conexão com PostgreSQL

Verificar se PostgreSQL está rodando:
```powershell
docker ps | findstr postgres
```

Deve mostrar `catalog-postgres-1` rodando na porta 5434.

### Erro de conexão com Redis

Verificar se Redis está rodando:
```powershell
docker ps | findstr redis
```

Deve mostrar `catalog-redis-1` rodando na porta 6381.
