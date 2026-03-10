# CORREÇÕES URGENTES - v1.0.5

## PROBLEMAS IDENTIFICADOS

1. ❌ **Tabela `settings` não existe** - migrations não foram executadas
2. ❌ **Worker não encontra as tasks** - faltava importar o módulo de tasks

## CORREÇÕES APLICADAS

### 1. Worker corrigido
Adicionado import das tasks no `worker.py`:
```python
from app.tasks import pdf_processor  # noqa
```

### 2. Script de migrations criado
Arquivo `run_migrations.sh` para facilitar execução das migrations.

## PASSOS PARA CORRIGIR NO SERVIDOR

### OPÇÃO 1: Rodar migrations diretamente (RECOMENDADO)

```bash
# Conectar no container da API
docker exec -it sixpet-catalog-api /bin/sh

# Dentro do container, rodar:
export DATABASE_URL="postgresql://sixpet:sixpet123@postgres:5432/sixpet_catalog"
alembic upgrade head

# Sair do container
exit
```

### OPÇÃO 2: Rodar migrations via psql (se a opção 1 falhar)

```bash
# Conectar no PostgreSQL
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# Copiar e colar este SQL:
CREATE TABLE IF NOT EXISTS settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description TEXT
);

CREATE INDEX IF NOT EXISTS ix_settings_id ON settings(id);
CREATE INDEX IF NOT EXISTS ix_settings_key ON settings(key);

INSERT INTO settings (key, value, value_type, description) VALUES
('groq_api_keys', '', 'string', 'Chaves de API Groq separadas por vírgula'),
('extractions_per_second', '10', 'int', 'Número de extrações por segundo no scraping'),
('scraping_url', '', 'string', 'URL base para web scraping'),
('scraping_enabled', 'false', 'bool', 'Habilitar web scraping automático'),
('max_concurrent_catalogs', '4', 'int', 'Número máximo de catálogos processados simultaneamente'),
('enable_deduplication', 'true', 'bool', 'Habilitar deduplicação automática'),
('similarity_threshold', '0.85', 'float', 'Limite de similaridade para deduplicação')
ON CONFLICT (key) DO NOTHING;

# Verificar
SELECT * FROM settings;

# Sair
\q
```

### 3. Aguardar build da v1.0.5

O build está rodando no GitHub Actions. Quando terminar:

1. No Portainer, fazer "Update the stack"
2. Marcar "Re-pull image and redeploy"
3. Clicar em "Update"

### 4. Verificar se funcionou

```bash
# Ver logs da API
docker logs sixpet-catalog-api --tail 50

# Ver logs do worker
docker logs sixpet-catalog-worker --tail 50

# Deve aparecer:
# [INFO] celery@... ready.
# (sem erro de "unregistered task")
```

### 5. Testar novamente

1. Acesse: https://catalog.sxconnect.com.br/dashboard/settings
2. Configure as chaves da API Groq
3. Configure a URL de scraping
4. Salve
5. Faça upload de um catálogo
6. Verifique o processamento

## VERIFICAÇÃO FINAL

```bash
# Ver status do catálogo
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT id, filename, status, products_found FROM catalogs ORDER BY id DESC LIMIT 5;"

# Ver settings
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT * FROM settings;"
```

## ORDEM DE EXECUÇÃO

1. ✅ Rodar migrations (OPÇÃO 1 ou 2 acima)
2. ⏳ Aguardar build v1.0.5 no GitHub Actions
3. ⏳ Fazer deploy no Portainer
4. ✅ Testar configurações
5. ✅ Testar upload e processamento

## VERSÕES

- Backend: v1.0.5 (corrige worker + migrations)
- Frontend: v1.0.1 (sem credenciais no login)
