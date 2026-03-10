# DEPLOY VERSÃO 1.0.4 - CORREÇÃO FINAL DO ENUM

## O QUE FOI CORRIGIDO

O problema era que o SQLAlchemy estava enviando o NOME do enum (`UPLOADED`) ao invés do VALOR (`uploaded`) para o PostgreSQL.

### Correção aplicada:

1. Adicionado método `__str__` no enum para forçar uso do valor
2. Configurado o Column com `values_callable` para garantir que apenas os valores sejam usados

```python
class CatalogStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    
    def __str__(self):
        return self.value
```

## PASSOS PARA DEPLOY

### 1. Aguardar Build no GitHub Actions

O build da versão v1.0.4 está sendo executado agora. Aguarde até que apareça a imagem:
- `ghcr.io/sxconnect/catalog:1.0.4`

Verifique em: https://github.com/SxConnect/catalog/actions

### 2. Atualizar no Portainer

No Portainer, na stack `sixpet-catalog`:

1. Clique em "Editor"
2. O arquivo já está atualizado para usar `1.0.4`
3. Clique em "Update the stack"
4. Marque "Re-pull image and redeploy"
5. Clique em "Update"

### 3. Verificar Logs

Após o deploy, verifique os logs:

```bash
# Logs da API
docker logs sixpet-catalog-api --tail 50 -f

# Logs do Worker
docker logs sixpet-catalog-worker --tail 50 -f
```

### 4. Testar Upload

1. Acesse: https://catalog.sxconnect.com.br
2. Faça login
3. Vá em "Upload de Catálogo"
4. Faça upload do arquivo `3-marca-parceira.pdf`
5. Deve aparecer "Processando..." sem erro

### 5. Verificar Processamento

No banco de dados:

```bash
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# Ver catálogos
SELECT id, filename, status, created_at FROM catalogs ORDER BY id DESC LIMIT 5;

# Sair
\q
```

## PROBLEMAS CONHECIDOS

### Worker com erro de autenticação Redis

O worker está tentando se autenticar no Redis, mas o Redis está configurado sem senha.

**Solução**: Já está corrigido no docker-compose.prod.yml:
```yaml
redis:
  command: redis-server --requirepass "" --protected-mode no
```

O worker deve conectar automaticamente após o restart.

## VERIFICAÇÃO FINAL

Após o deploy da v1.0.4, o sistema deve estar 100% funcional:

- ✅ Frontend acessível
- ✅ Login funcionando
- ✅ API Keys funcionando
- ✅ Página de produtos funcionando
- ✅ Upload de catálogo funcionando
- ✅ Processamento assíncrono funcionando
- ✅ Worker Celery conectado

## VERSÕES

- Backend API: v1.0.4
- Frontend: v1.0.0
- PostgreSQL: 15-alpine
- Redis: 7-alpine

## PRÓXIMOS PASSOS

Após confirmar que o upload funciona:

1. Testar processamento completo de um catálogo
2. Verificar extração de produtos
3. Testar busca e filtros
4. Testar exportação CSV
5. Configurar backup automático do PostgreSQL
