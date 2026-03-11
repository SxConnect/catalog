# 🐳 Correção via Portainer - Problemas de Rate Limiting

## 🚨 **Problema Corrigido:**
- Funções com `@rate_limit_products()` não tinham parâmetro `Request`
- Código já foi corrigido e enviado para o GitHub
- Nova imagem será buildada automaticamente

## 🚀 **PASSOS NO PORTAINER:**

### **Passo 1: Aguardar Build (2-3 minutos)**
1. Verificar se o build terminou: https://github.com/SxConnect/catalog/actions
2. Aguardar ícone verde ✅ nos workflows

### **Passo 2: Excluir Containers no Portainer**
1. **Ir para**: Containers
2. **Selecionar**: 
   - ☑️ `sixpet-catalog-api`
   - ☑️ `sixpet-catalog-frontend` 
   - ☑️ `sixpet-catalog-worker`
3. **Clicar**: Remove (🗑️)
4. **Confirmar**: Remove

### **Passo 3: Fazer Deploy via Portainer**
1. **Ir para**: Stacks
2. **Selecionar**: `catalog` (ou nome da sua stack)
3. **Clicar**: Update the stack
4. **Verificar**: Se o docker-compose.prod.yml está correto
5. **Clicar**: Update the stack
6. **Aguardar**: Deploy completar

### **Passo 4: Verificar Containers**
1. **Ir para**: Containers
2. **Verificar status**:
   - ✅ `sixpet-catalog-api` - healthy
   - ✅ `sixpet-catalog-frontend` - healthy
   - ✅ `sixpet-catalog-worker` - running
   - ✅ `sixpet-catalog-postgres` - healthy
   - ✅ `sixpet-catalog-redis` - healthy

### **Passo 5: Executar Migrações**
1. **Clicar** em `sixpet-catalog-api`
2. **Ir para**: Console
3. **Executar**: `alembic upgrade head`
4. **Aguardar**: Migrações completarem

---

## 🔍 **Verificações Pós-Deploy:**

### **1. Testar Backend:**
- URL: https://catalog-api.sxconnect.com.br/health
- Deve retornar: `{"status": "healthy"}`

### **2. Testar Frontend:**
- URL: https://catalog.sxconnect.com.br
- Dashboard deve carregar sem erros no console

### **3. Verificar Logs no Portainer:**
**Backend (`sixpet-catalog-api`):**
- Deve mostrar: "Uvicorn running on http://0.0.0.0:8000"
- Sem erros de "No request argument"

**Frontend (`sixpet-catalog-frontend`):**
- Deve mostrar: "ready - started server on 0.0.0.0:3000"
- Sem erros de conexão

---

## ⚠️ **Se Ainda Houver Problemas:**

### **Logs para Verificar:**
1. **No Portainer**: Containers → Clicar no container → Logs
2. **Procurar por**:
   - ❌ Erros de "No request argument" 
   - ❌ Erros de conexão
   - ❌ Erros de CORS

### **Comandos de Emergência (Console do Container):**
```bash
# No console do sixpet-catalog-api
alembic upgrade head
python -c "from app.main import app; print('App loaded successfully')"

# No console do sixpet-catalog-frontend  
curl http://localhost:3000/api/health
```

---

## 📊 **Resultado Esperado:**

### **✅ Sucesso - Você deve ver:**
- Todos os containers com status "healthy" ou "running"
- Backend respondendo em `/health`
- Frontend carregando dashboard sem erros
- Console do navegador limpo (sem erros vermelhos)

### **❌ Se ainda houver problemas:**
- Verificar logs específicos no Portainer
- Reportar erro exato encontrado
- Posso ajudar com correções adicionais

---

## 🎯 **EXECUTE AGORA:**

1. ⏳ **Aguardar build** (verificar GitHub Actions)
2. 🗑️ **Excluir containers** no Portainer
3. 🚀 **Deploy da stack** no Portainer
4. ✅ **Verificar status** dos containers
5. 🗄️ **Executar migrações** no console da API
6. 🌐 **Testar frontend** no navegador

**Reporte o resultado após executar!** 📋