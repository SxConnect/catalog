# 🔧 Executar Migrações na VPS

## 🚨 **PROBLEMA IDENTIFICADO**

```
column products_catalog.ingredients does not exist
```

A migração 004 que adiciona os campos `ingredients` e `nutritional_info` não foi executada na VPS.

## 🎯 **SOLUÇÃO**

### **Opção 1: Via Portainer (Recomendado)**

1. **Acessar Portainer**
2. **Ir em Containers → sixpet-catalog-api**
3. **Clicar em "Console"**
4. **Executar comando:**

```bash
alembic upgrade head
```

### **Opção 2: Via Docker Exec**

```bash
docker exec -it sixpet-catalog-api alembic upgrade head
```

### **Opção 3: Restart do Container**

O container da API executa migrações automaticamente na inicialização:

1. **Portainer → Containers → sixpet-catalog-api**
2. **Restart**
3. **Verificar logs** para confirmar execução das migrações

## 🔍 **VERIFICAR SE FUNCIONOU**

### **1. Verificar Logs do Container**
```bash
docker logs sixpet-catalog-api -f
```

Deve mostrar:
```
INFO  [alembic.runtime.migration] Running upgrade xxx -> 004, add_nutritional_fields
```

### **2. Testar Upload**
- Fazer upload de um PDF
- Verificar se não há mais erro de coluna inexistente

### **3. Verificar Banco Diretamente**
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'products_catalog' 
AND column_name IN ('ingredients', 'nutritional_info');
```

## 📋 **MIGRAÇÕES PENDENTES**

### **Migração 004: add_nutritional_fields**
```sql
-- Adiciona colunas para ingredientes e informações nutricionais
ALTER TABLE products_catalog 
ADD COLUMN ingredients TEXT,
ADD COLUMN nutritional_info JSONB;
```

### **Outras Migrações:**
- 001: initial_schema ✅
- 002: add_settings_table ✅  
- 003: fix_catalog_status_enum ✅
- 004: add_nutritional_fields ❌ **PENDENTE**
- 005: add_paused_status ✅

## ⚠️ **IMPORTANTE**

### **Backup Automático**
O PostgreSQL no Portainer já tem backup automático configurado.

### **Zero Downtime**
As migrações são seguras e não causam downtime:
- `ADD COLUMN` é operação não-bloqueante
- Colunas são opcionais (nullable)

### **Rollback (se necessário)**
```bash
# Voltar para migração anterior
alembic downgrade -1
```

## 🚀 **APÓS EXECUTAR**

### **Resultado Esperado:**
- ✅ Upload de PDF funcionando
- ✅ Sem erros de "column does not exist"
- ✅ Campos ingredients e nutritional_info disponíveis
- ✅ Sistema de parsing nutricional funcionando

### **Funcionalidades Habilitadas:**
- Extração de ingredientes de PDFs
- Parsing de tabelas nutricionais
- Endpoints de busca por ingrediente
- Comparação nutricional de produtos

---

**Status**: ⚠️ **MIGRAÇÃO PENDENTE NA VPS**  
**Ação**: Executar `alembic upgrade head` no container da API  
**ETA**: 30 segundos para executar migração