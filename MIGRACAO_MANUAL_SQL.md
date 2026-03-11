# 🔧 MIGRAÇÃO MANUAL - SQL DIRETO

## 🚨 **EXECUTE ESTE SQL NO BANCO POSTGRESQL**

### **Opção 1: Via Portainer PostgreSQL Console**

1. **Portainer → Containers → `sixpet-catalog-postgres`**
2. **Console**
3. **Executar:**

```bash
psql -U sixpet -d sixpet_catalog
```

4. **Executar este SQL:**

```sql
-- Adicionar colunas ingredients e nutritional_info
ALTER TABLE products_catalog 
ADD COLUMN IF NOT EXISTS ingredients TEXT,
ADD COLUMN IF NOT EXISTS nutritional_info JSONB;

-- Verificar se as colunas foram criadas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products_catalog' 
AND column_name IN ('ingredients', 'nutritional_info');

-- Atualizar versão do Alembic
INSERT INTO alembic_version (version_num) VALUES ('004') 
ON CONFLICT (version_num) DO NOTHING;

-- Confirmar
SELECT * FROM alembic_version;
```

### **Opção 2: Via pgAdmin ou Cliente SQL**

Execute o mesmo SQL acima.

### **Opção 3: Via Docker Exec**

```bash
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "
ALTER TABLE products_catalog 
ADD COLUMN IF NOT EXISTS ingredients TEXT,
ADD COLUMN IF NOT EXISTS nutritional_info JSONB;

INSERT INTO alembic_version (version_num) VALUES ('004') 
ON CONFLICT (version_num) DO NOTHING;
"
```

## ✅ **RESULTADO ESPERADO**

Após executar, deve mostrar:
```
 column_name     | data_type 
-----------------+-----------
 ingredients     | text
 nutritional_info| jsonb
```

## 🎯 **DEPOIS DISSO**

- ✅ Upload vai funcionar
- ✅ Sem mais erros de coluna inexistente
- ✅ Sistema 100% funcional

**EXECUTE O SQL E ME CONFIRME!**