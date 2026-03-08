# 🚀 REDEPLOY AGORA - Instruções Diretas

## Status Atual
✅ Commit `40245ea` enviado para GitHub
⏳ Build do GitHub Actions em andamento
⏳ Aguardando imagens no GHCR

## O Que Foi Corrigido

1. **CORS** - Agora aceita requisições do frontend
2. **API Keys** - Endpoint aceita JSON corretamente
3. **Headers** - Todos os headers necessários configurados

## Passo a Passo para Redeploy

### 1. Aguardar Build (5-10 minutos)
Verificar em: https://github.com/SxConnect/catalog/actions

Quando aparecer ✅ verde, prosseguir para o passo 2.

### 2. No Portainer

**Opção Simples (Recomendada):**
1. Ir em **Stacks** > **sixpet-catalog**
2. Clicar em **Pull and redeploy**
3. Aguardar containers reiniciarem

**Opção Manual:**
1. Ir em **Containers**
2. Selecionar:
   - `sixpet-catalog-api`
   - `sixpet-catalog-frontend`
   - `sixpet-catalog-worker`
3. Clicar em **Recreate**
4. Marcar **Pull latest image**
5. Clicar em **Recreate**

### 3. Verificar se Funcionou

**Abrir no navegador:**
- https://catalog.sxconnect.com.br

**Abrir Console (F12):**
- NÃO deve ter erros de CORS
- NÃO deve ter "Access-Control-Allow-Origin"
- NÃO deve ter "422 Unprocessable Entity"

**Testar funcionalidades:**
1. Fazer login
2. Ir em **API Keys** - adicionar uma chave
3. Ir em **Settings** - salvar configurações
4. Ir em **Upload** - fazer upload de PDF
5. Ir em **Produtos** - ver lista de produtos

## Se Ainda Houver Erros

### Verificar Logs do Backend
```bash
docker logs sixpet-catalog-api --tail 50
```

### Verificar Logs do Frontend
```bash
docker logs sixpet-catalog-frontend --tail 50
```

### Verificar se Imagens Foram Atualizadas
```bash
docker images | grep catalog
```

Deve mostrar imagens recentes (minutos/horas atrás, não dias).

### Forçar Pull Manual
```bash
docker pull ghcr.io/sxconnect/catalog:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

## Erros Esperados (Resolvidos)

❌ **ANTES:**
```
Access to XMLHttpRequest blocked by CORS policy
Failed to load resource: 422
Failed to load resource: net::ERR_FAILED
```

✅ **DEPOIS:**
```
Status 200 OK
Requisições funcionando normalmente
Console limpo sem erros
```

## Contato

Se após seguir todos os passos ainda houver problemas, enviar:
1. Screenshot do console do navegador (F12)
2. Logs do backend: `docker logs sixpet-catalog-api --tail 100`
3. Logs do frontend: `docker logs sixpet-catalog-frontend --tail 100`

---

**IMPORTANTE:** Aguardar o build do GitHub Actions completar antes de fazer redeploy!
