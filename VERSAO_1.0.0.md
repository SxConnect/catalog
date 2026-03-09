# 🎉 Versão 1.0.0 - Release

## O Que Foi Feito

Sistema completo com versionamento semântico. Agora usamos tags de versão (v1.0.0) ao invés de `latest` ou SHA.

## Imagens da Versão 1.0.0

- **Backend/Worker**: `ghcr.io/sxconnect/catalog:1.0.0`
- **Frontend**: `ghcr.io/sxconnect/catalog-frontend:1.0.0`

## Status do Build

Verificar em: https://github.com/SxConnect/catalog/actions

Aguardar até aparecer ✅ verde nos workflows disparados pela tag `v1.0.0`.

## Como Fazer Deploy

### 1. Aguardar Builds Completarem

Os workflows foram disparados automaticamente quando criamos a tag `v1.0.0`.

Aguarde até ver:
- ✅ Build and Push Docker Image (tag v1.0.0)
- ✅ Build and Push Frontend Docker Image (tag v1.0.0)

### 2. Limpar Imagens Antigas (OPCIONAL)

Se quiser limpar as imagens antigas do GHCR:

1. Ir em: https://github.com/orgs/SxConnect/packages
2. Encontrar `catalog` e `catalog-frontend`
3. Deletar versões antigas (manter apenas 1.0.0 e latest)

### 3. No Portainer - Fazer Deploy

**Opção A - Via Stack:**
1. Ir em **Stacks** > **sixpet-catalog**
2. Clicar em **Editor**
3. Verificar se está assim:
   ```yaml
   api:
     image: ghcr.io/sxconnect/catalog:1.0.0
   
   worker:
     image: ghcr.io/sxconnect/catalog:1.0.0
   
   frontend:
     image: ghcr.io/sxconnect/catalog-frontend:1.0.0
   ```
4. Clicar em **Update the stack**
5. Marcar **Pull and redeploy**

**Opção B - Via CLI:**
```bash
cd /caminho/do/projeto
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### 4. Verificar

```bash
# Ver se containers estão rodando
docker ps | grep sixpet

# Ver versão das imagens
docker images | grep catalog

# Ver logs
docker logs sixpet-catalog-api --tail 50
docker logs sixpet-catalog-frontend --tail 50

# Testar API
curl https://catalog-api.sxconnect.com.br/health
```

### 5. Testar no Navegador

Abrir: https://catalog.sxconnect.com.br

- ✅ Login funciona
- ✅ Dashboard carrega
- ✅ Tema dark aplicado
- ✅ Todas as páginas funcionam
- ✅ Console sem erros de CORS
- ✅ API responde corretamente

## Funcionalidades da v1.0.0

✅ Sistema de autenticação
✅ Dashboard com estatísticas
✅ Upload de catálogos PDF
✅ Processamento automático via IA (Groq)
✅ Listagem de produtos com filtros
✅ Busca e ordenação
✅ Exportação CSV
✅ Gerenciamento de API Keys
✅ Configurações do sistema
✅ Web scraping para enriquecimento
✅ Tema dark completo
✅ CORS configurado corretamente
✅ Logging estruturado
✅ Worker Celery para processamento assíncrono

## Próximas Versões

Para criar uma nova versão:

```bash
# Fazer alterações no código
git add .
git commit -m "feat: Nova funcionalidade"
git push origin main

# Criar nova tag
git tag -a v1.1.0 -m "Release 1.1.0 - Descrição"
git push origin v1.1.0

# Atualizar docker-compose.prod.yml
# Mudar de 1.0.0 para 1.1.0

# Aguardar build e fazer redeploy
```

## Versionamento Semântico

- **MAJOR** (1.x.x): Mudanças incompatíveis na API
- **MINOR** (x.1.x): Novas funcionalidades compatíveis
- **PATCH** (x.x.1): Correções de bugs

Exemplos:
- `v1.0.0` → `v1.0.1`: Correção de bug
- `v1.0.0` → `v1.1.0`: Nova funcionalidade
- `v1.0.0` → `v2.0.0`: Mudança incompatível

## Rollback

Se algo der errado, voltar para versão anterior:

```yaml
api:
  image: ghcr.io/sxconnect/catalog:1.0.0  # Versão estável
```

E fazer redeploy.

## Suporte

Se tiver problemas:
1. Verificar logs dos containers
2. Verificar se imagens foram baixadas corretamente
3. Verificar se Traefik está roteando
4. Testar endpoints diretamente
