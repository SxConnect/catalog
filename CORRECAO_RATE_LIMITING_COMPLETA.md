# Correção Completa dos Rate Limits - Executar via Portainer

## ✅ CORREÇÕES APLICADAS

Todas as funções com decoradores `@rate_limit_*()` foram corrigidas:

### Arquivos Corrigidos:
- `catalog/app/api/admin.py` - 6 funções corrigidas
- `catalog/app/api/health.py` - 7 funções corrigidas  
- `catalog/app/api/deduplication.py` - 4 funções corrigidas
- `catalog/app/api/products.py` - 9 funções corrigidas
- `catalog/app/api/catalog.py` - 3 funções já estavam corretas

### Commit Realizado:
```
c7f3658 - fix: adicionar parâmetro request em todas as funções com rate limiting
```

## 🚀 INSTRUÇÕES PARA DEPLOY VIA PORTAINER

### 1. Acessar Portainer
- Acesse seu Portainer na VPS
- Vá para **Stacks** → **catalog-stack**

### 2. Parar e Remover Containers
- Clique em **Stop** na stack
- Aguarde todos os containers pararem
- Clique em **Remove** (mantenha volumes se quiser preservar dados)

### 3. Recriar Stack
- Clique em **Deploy the stack** 
- Ou use **Add stack** se removeu completamente
- Use o mesmo `docker-compose.prod.yml`

### 4. Verificar Logs
Após deploy, verificar logs dos containers:

```bash
# Via Portainer: Containers → catalog-api → Logs
# Ou via SSH na VPS:
docker logs catalog-api
```

**Logs esperados (SEM ERROS):**
```
INFO: Will watch for changes in these directories: ['/app']
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO: Started reloader process [1] using WatchFiles
INFO: Started server process [X]
INFO: Waiting for application startup.
INFO: Application startup complete.
```

## 🔍 VERIFICAÇÃO DE FUNCIONAMENTO

### 1. Health Check
```bash
curl http://localhost:8000/api/health/
```

### 2. Teste de API
```bash
curl http://localhost:8000/api/products/search?q=test
```

### 3. Frontend
- Acesse: `http://seu-dominio:3000`
- Teste login e navegação

## ⚠️ SE AINDA HOUVER PROBLEMAS

### Logs para Verificar:
1. **API Container**: `docker logs catalog-api`
2. **Worker Container**: `docker logs catalog-worker`  
3. **Frontend Container**: `docker logs catalog-frontend`

### Problemas Possíveis:
- **Conectividade**: Verificar se containers estão na mesma rede
- **Variáveis de ambiente**: Verificar se `.env` está correto
- **Banco de dados**: Verificar se PostgreSQL está funcionando

## 📋 CHECKLIST FINAL

- [ ] Stack parada via Portainer
- [ ] Containers removidos
- [ ] Stack recriada com sucesso
- [ ] API iniciando sem erros de rate limiting
- [ ] Health check respondendo
- [ ] Frontend carregando
- [ ] Conectividade frontend-backend funcionando

## 🎯 RESULTADO ESPERADO

Após seguir estas instruções:
- ✅ API iniciará sem erros de rate limiting
- ✅ Todos os endpoints funcionarão corretamente
- ✅ Frontend conseguirá se comunicar com a API
- ✅ Sistema totalmente funcional

---

**Data da correção**: 11/03/2026
**Commit**: c7f3658 - fix: adicionar parâmetro request em todas as funções com rate limiting