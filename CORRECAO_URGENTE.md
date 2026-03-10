# CORREÇÃO URGENTE - PROBLEMA DE AUTENTICAÇÃO

## PROBLEMA IDENTIFICADO

O erro `password authentication failed for user "sixpet"` acontece porque:

1. O container da API está rodando com as variáveis de ambiente corretas
2. Mas quando você executa `alembic upgrade head` DENTRO do container, o Alembic não consegue ler as variáveis de ambiente
3. O Alembic está tentando usar a senha padrão do `alembic.ini` que está incorreta

## SOLUÇÃO IMEDIATA

Execute este comando no servidor:

```bash
cd /root
bash fix_database.sh
```

Este script vai:
1. Conectar diretamente no PostgreSQL (sem usar Alembic)
2. Corrigir o ENUM do status
3. Verificar se a API está funcionando

## ALTERNATIVA (se o script não funcionar)

Execute manualmente:

```bash
# 1. Conectar no PostgreSQL
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# 2. Executar SQL (copie e cole tudo de uma vez):
ALTER TABLE catalogs ALTER COLUMN status TYPE text;
DROP TYPE IF EXISTS catalogstatus CASCADE;
CREATE TYPE catalogstatus AS ENUM ('uploaded', 'processing', 'completed', 'failed');
UPDATE catalogs SET status = LOWER(status) WHERE status IS NOT NULL;
ALTER TABLE catalogs ALTER COLUMN status TYPE catalogstatus USING status::catalogstatus;
ALTER TABLE catalogs ALTER COLUMN status SET DEFAULT 'uploaded';

# 3. Verificar
SELECT column_name, data_type, udt_name 
FROM information_schema.columns 
WHERE table_name = 'catalogs' AND column_name = 'status';

# 4. Sair
\q
```

## POR QUE NÃO USAR ALEMBIC?

O Alembic precisa de configuração adicional para ler as variáveis de ambiente dentro do container. Como a API já está rodando e funcionando, é mais rápido corrigir o banco diretamente.

## APÓS A CORREÇÃO

1. Reinicie o container da API:
   ```bash
   docker restart sixpet-catalog-api
   ```

2. Teste o upload:
   - Acesse: https://catalog.sxconnect.com.br
   - Faça login
   - Vá em "Upload de Catálogo"
   - Faça upload de um PDF pequeno (teste)

## VERIFICAÇÃO

Para confirmar que está funcionando:

```bash
# Ver logs da API
docker logs sixpet-catalog-api --tail 50 -f

# Ver logs do worker
docker logs sixpet-catalog-worker --tail 50 -f
```

Quando fizer o upload, você deve ver logs de processamento.
