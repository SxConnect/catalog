# 🔄 Atualização VPS - SixPet Catalog Engine

## ✅ Alterações Implementadas

**Data:** 11 de março de 2026  
**Commit:** Atualização para imagens GHCR

### 🐳 **Imagens Atualizadas no docker-compose.prod.yml:**

**ANTES:**
```yaml
api:
  image: ghcr.io/sxconnect/catalog:1.0.7

worker:
  image: ghcr.io/sxconnect/catalog:1.0.7

frontend:
  image: ghcr.io/sxconnect/catalog-frontend:1.0.3
```

**DEPOIS:**
```yaml
api:
  image: ghcr.io/sxconnect/catalog-backend:latest

worker:
  image: ghcr.io/sxconnect/catalog-backend:latest

frontend:
  image: ghcr.io/sxconnect/catalog-frontend:latest
```

## 🚀 Como Atualizar na VPS

### **Opção 1: Script Automático (Recomendado)**

```bash
# Baixar arquivos atualizados
git pull origin main

# Executar script de atualização
./update-production.sh  # Linux
./update-production.ps1 # Windows
```

### **Opção 2: Manual**

```bash
# 1. Baixar arquivos atualizados
git pull origin main

# 2. Parar serviços da aplicação (mantém banco/redis)
docker-compose -f docker-compose.prod.yml stop api worker frontend

# 3. Baixar imagens mais recentes
docker pull ghcr.io/sxconnect/catalog-backend:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# 4. Remover containers antigos
docker-compose -f docker-compose.prod.yml rm -f api worker frontend

# 5. Subir serviços atualizados
docker-compose -f docker-compose.prod.yml up -d api worker frontend

# 6. Executar migrações
docker exec sixpet-catalog-api alembic upgrade head

# 7. Verificar status
docker-compose -f docker-compose.prod.yml ps
```

## 🔍 **Verificações Pós-Atualização**

### **1. Status dos Containers:**
```bash
docker-compose -f docker-compose.prod.yml ps
```

**Esperado:**
```
NAME                     IMAGE                                    STATUS
sixpet-catalog-api       ghcr.io/sxconnect/catalog-backend:latest   Up
sixpet-catalog-frontend  ghcr.io/sxconnect/catalog-frontend:latest  Up
sixpet-catalog-worker    ghcr.io/sxconnect/catalog-backend:latest   Up
sixpet-catalog-postgres  postgres:15-alpine                       Up
sixpet-catalog-redis     redis:7-alpine                           Up
```

### **2. Saúde dos Serviços:**
```bash
# Backend
curl -f https://catalog-api.sxconnect.com.br/health

# Frontend
curl -f https://catalog.sxconnect.com.br/api/health
```

### **3. Logs dos Serviços:**
```bash
# Backend
docker logs --tail 20 sixpet-catalog-api

# Frontend
docker logs --tail 20 sixpet-catalog-frontend

# Worker
docker logs --tail 20 sixpet-catalog-worker
```

## 🎯 **Benefícios da Atualização**

### ✅ **Imagens Sempre Atualizadas:**
- Tag `:latest` sempre puxa a versão mais recente
- Builds automáticos no GitHub Actions
- Sem necessidade de alterar versões manualmente

### ✅ **Nomenclatura Consistente:**
- `catalog-backend` para API e Worker
- `catalog-frontend` para interface web
- Separação clara entre componentes

### ✅ **Deploy Simplificado:**
- Script de atualização automatizado
- Backup automático do estado atual
- Verificações de saúde integradas

## 🛠️ **Comandos Úteis Pós-Atualização**

```bash
# Ver todas as imagens
docker images | grep ghcr.io/sxconnect

# Limpar imagens antigas
docker image prune -f

# Reiniciar serviço específico
docker restart sixpet-catalog-api

# Ver logs em tempo real
docker logs -f sixpet-catalog-api

# Status completo
docker-compose -f docker-compose.prod.yml ps
docker stats --no-stream
```

## 🔄 **Processo de Atualização Futuro**

### **Automático via CI/CD:**
1. Push para `main` → GitHub Actions build
2. Imagens atualizadas no GHCR
3. Na VPS: `./update-production.sh`
4. Serviços atualizados automaticamente

### **Rollback se Necessário:**
```bash
# Voltar para versão específica
docker-compose -f docker-compose.prod.yml stop api worker frontend
docker pull ghcr.io/sxconnect/catalog-backend:v1.0.7
# Editar docker-compose.prod.yml temporariamente
docker-compose -f docker-compose.prod.yml up -d api worker frontend
```

## ✅ **Resultado Esperado**

Após a atualização, o sistema deve estar rodando com:

- ✅ **Backend**: `ghcr.io/sxconnect/catalog-backend:latest`
- ✅ **Frontend**: `ghcr.io/sxconnect/catalog-frontend:latest`
- ✅ **URLs funcionando**: 
  - https://catalog.sxconnect.com.br
  - https://catalog-api.sxconnect.com.br
- ✅ **Todas as funcionalidades preservadas**
- ✅ **Performance mantida ou melhorada**

---

**A VPS agora está configurada para receber atualizações automáticas das imagens mais recentes!** 🚀