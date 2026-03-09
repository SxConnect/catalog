# 🚀 Deploy com Tags SHA

## O Que Mudou

Agora usamos tags SHA ao invés de `latest` para garantir que sempre pegamos a versão correta das imagens.

## Commits Atuais

- **Backend/Worker**: `ghcr.io/sxconnect/catalog:04adc7e`
- **Frontend**: `ghcr.io/sxconnect/catalog-frontend:04adc7e`

## Como Fazer Deploy

### 1. Aguardar Build do GitHub Actions

Verificar em: https://github.com/SxConnect/catalog/actions

Aguardar até aparecer ✅ verde nos dois workflows:
- Build and Push Docker Image (backend)
- Build and Push Frontend Docker Image (frontend)

### 2. No Portainer

**Opção A - Recriar Stack:**
1. Ir em **Stacks** > **sixpet-catalog**
2. Clicar em **Editor**
3. Verificar se as tags estão corretas:
   ```yaml
   api:
     image: ghcr.io/sxconnect/catalog:04adc7e
   
   worker:
     image: ghcr.io/sxconnect/catalog:04adc7e
   
   frontend:
     image: ghcr.io/sxconnect/catalog-frontend:04adc7e
   ```
4. Clicar em **Update the stack**
5. Marcar **Pull and redeploy**

**Opção B - Via CLI:**
```bash
cd /caminho/do/projeto
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Verificar

```bash
# Ver se containers estão rodando
docker ps | grep sixpet

# Ver logs
docker logs sixpet-catalog-api --tail 50
docker logs sixpet-catalog-frontend --tail 50

# Testar API
curl https://catalog-api.sxconnect.com.br/health
```

### 4. Testar no Navegador

Abrir: https://catalog.sxconnect.com.br

- Fazer login
- Testar todas as páginas
- Verificar console (F12) - não deve ter erros

## Próximos Deploys

Sempre que fizer um novo commit:

1. Aguardar build completar
2. Pegar o SHA do commit: `git rev-parse --short HEAD`
3. Atualizar `docker-compose.prod.yml` com o novo SHA
4. Fazer commit e push
5. Aguardar novo build
6. Fazer redeploy no Portainer

## Vantagens

✅ Sempre sabe qual versão está rodando
✅ Não pega versão errada do cache
✅ Pode fazer rollback facilmente mudando o SHA
✅ Rastreabilidade completa

## Rollback

Se algo der errado, basta mudar para o SHA anterior:

```yaml
api:
  image: ghcr.io/sxconnect/catalog:79cf722  # SHA anterior
```

E fazer redeploy.
