# Deploy v1.0.7 - Sitemap Import + Real-time Monitoring

## 🎯 Novidades desta Versão

### Backend (v1.0.7)
- ✅ Importação via Sitemap XML
- ✅ API de monitoramento em tempo real
- ✅ Endpoints de status de processamento
- ✅ Dependências para web scraping (httpx, beautifulsoup4, lxml)
- ✅ Dockerfile atualizado com libxml2-dev e libxslt-dev

### Frontend (v1.0.3)
- ✅ Interface de importação via sitemap (`/dashboard/sitemap`)
- ✅ Monitoramento em tempo real de uploads
- ✅ Barra de progresso com estimativa de tempo
- ✅ Histórico de uploads recentes
- ✅ Link no menu para importação via sitemap

## 🚀 Deploy Rápido

### Opção 1: Script Automático (Recomendado)

```bash
# 1. Dar permissão (primeira vez)
chmod +x release.sh

# 2. Executar release
./release.sh 1.0.7 1.0.3

# 3. Aguardar GitHub Actions completar (2-5 minutos)
# Ver em: https://github.com/sxconnect/catalog/actions

# 4. No servidor
ssh usuario@servidor
cd /caminho/do/projeto
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Opção 2: Manual

```bash
# 1. Commit e push
git add .
git commit -m "feat: add sitemap import and real-time monitoring v1.0.7"
git push origin main

# 2. Criar tags
git tag v1.0.7
git tag frontend-v1.0.3
git push origin v1.0.7
git push origin frontend-v1.0.3

# 3. Aguardar GitHub Actions
# Ver em: https://github.com/sxconnect/catalog/actions

# 4. Verificar imagens no GHCR
# https://github.com/orgs/sxconnect/packages
# Deve aparecer:
#   - ghcr.io/sxconnect/catalog:1.0.7
#   - ghcr.io/sxconnect/catalog-frontend:1.0.3

# 5. No servidor
ssh usuario@servidor
cd /caminho/do/projeto

# Atualizar docker-compose.prod.yml
nano docker-compose.prod.yml
# Mudar versões para:
#   api: ghcr.io/sxconnect/catalog:1.0.7
#   worker: ghcr.io/sxconnect/catalog:1.0.7
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.3

# Pull e restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 📝 Atualizar docker-compose.prod.yml

```yaml
services:
  api:
    image: ghcr.io/sxconnect/catalog:1.0.7  # ← v1.0.6 → v1.0.7
    container_name: sixpet-catalog-api
    # ... resto da config

  worker:
    image: ghcr.io/sxconnect/catalog:1.0.7  # ← v1.0.6 → v1.0.7
    container_name: sixpet-catalog-worker
    # ... resto da config

  frontend:
    image: ghcr.io/sxconnect/catalog-frontend:1.0.3  # ← v1.0.2 → v1.0.3
    container_name: sixpet-catalog-frontend
    # ... resto da config
```

## 🧪 Testes Pós-Deploy

### 1. Health Checks
```bash
# API
curl https://catalog-api.sxconnect.com.br/health
# Esperado: {"status":"healthy"}

# Frontend
curl https://catalog.sxconnect.com.br/api/health
# Esperado: {"status":"ok"}

# Stats
curl https://catalog-api.sxconnect.com.br/api/status/stats
# Esperado: JSON com estatísticas
```

### 2. Testar Upload com Monitoramento
1. Acesse: `https://catalog.sxconnect.com.br/dashboard/upload`
2. Faça upload de um PDF pequeno (5-10 páginas)
3. Verifique se aparece:
   - ✅ Barra de progresso
   - ✅ "Página X de Y"
   - ✅ "N produtos encontrados"
   - ✅ "Tempo estimado: Xm Ys"
4. Aguarde conclusão
5. Verifique mensagem de sucesso com resumo

### 3. Testar Importação via Sitemap
```bash
# Preview (via API)
curl -X POST https://catalog-api.sxconnect.com.br/api/sitemap/preview \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 5
  }'

# Testar scraping de uma URL
curl -X POST https://catalog-api.sxconnect.com.br/api/sitemap/test-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"
  }'
```

**Via Frontend:**
1. Acesse: `https://catalog.sxconnect.com.br/dashboard/sitemap`
2. Cole URL: `https://www.bbbpet.com.br/sitemap.xml`
3. Filtro: `/produto/`
4. Max produtos: `10`
5. Clique "Preview" → deve mostrar 10 URLs
6. Clique "Testar" em uma URL → deve mostrar dados extraídos
7. Clique "Importar Produtos" → aguarde conclusão

### 4. Verificar Logs
```bash
# Ver últimos logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f frontend

# Verificar erros
docker-compose -f docker-compose.prod.yml logs | grep -i error
```

## 📊 Novos Endpoints

### Status e Monitoramento
```bash
# Status de um catálogo específico
GET /api/status/catalog/{id}/status

# Produtos de um catálogo
GET /api/status/catalog/{id}/products

# Catálogos recentes
GET /api/status/recent?limit=10

# Estatísticas gerais
GET /api/status/stats
```

### Sitemap
```bash
# Preview de sitemap
POST /api/sitemap/preview
{
  "sitemap_url": "https://exemplo.com/sitemap.xml",
  "url_filter": "/produto/",
  "max_urls": 10
}

# Testar scraping de URL
POST /api/sitemap/test-scrape
{
  "url": "https://exemplo.com/produto/123"
}

# Importar produtos
POST /api/sitemap/import
{
  "sitemap_url": "https://exemplo.com/sitemap.xml",
  "catalog_id": 1,
  "url_filter": "/produto/",
  "max_products": 50,
  "auto_save": true
}
```

## 🔄 Rollback (se necessário)

Se algo der errado:

```bash
# 1. Editar docker-compose.prod.yml
nano docker-compose.prod.yml

# Voltar para versões anteriores:
#   api: ghcr.io/sxconnect/catalog:1.0.6
#   worker: ghcr.io/sxconnect/catalog:1.0.6
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.2

# 2. Aplicar
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 3. Verificar
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## 🗄️ Backup (Recomendado antes do deploy)

```bash
# Backup do banco de dados
docker exec sixpet-catalog-postgres pg_dump -U sixpet sixpet_catalog > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup dos volumes
docker run --rm -v catalog_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
docker run --rm -v catalog_storage:/data -v $(pwd):/backup alpine tar czf /backup/storage_backup_$(date +%Y%m%d).tar.gz /data
```

## 📋 Checklist de Deploy

- [ ] Código commitado e pushed
- [ ] Tags criadas (v1.0.7 e frontend-v1.0.3)
- [ ] GitHub Actions completou builds
- [ ] Imagens disponíveis no GHCR
- [ ] Backup do banco de dados feito
- [ ] docker-compose.prod.yml atualizado
- [ ] Pull das novas imagens
- [ ] Serviços reiniciados
- [ ] Health checks passando
- [ ] Upload com monitoramento testado
- [ ] Importação via sitemap testada
- [ ] Logs verificados (sem erros críticos)
- [ ] Documentação atualizada

## 🐛 Troubleshooting

### GitHub Actions falhou
```bash
# Ver logs
https://github.com/sxconnect/catalog/actions

# Recriar tag e push novamente
git tag -d v1.0.7
git push origin :refs/tags/v1.0.7
git tag v1.0.7
git push origin v1.0.7
```

### Imagem não encontrada no GHCR
```bash
# Verificar se existe
docker pull ghcr.io/sxconnect/catalog:1.0.7

# Se não existir, verificar:
# 1. GitHub Actions completou?
# 2. Tag foi criada corretamente?
# 3. Permissões do GHCR estão OK?
```

### Serviço não inicia
```bash
# Ver logs detalhados
docker-compose -f docker-compose.prod.yml logs api

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml config

# Restart forçado
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Worker não processa
```bash
# Verificar status
docker-compose -f docker-compose.prod.yml ps worker

# Ver logs
docker-compose -f docker-compose.prod.yml logs worker

# Verificar Redis
docker-compose -f docker-compose.prod.yml logs redis

# Restart
docker-compose -f docker-compose.prod.yml restart worker redis
```

### Sitemap não funciona
```bash
# Testar manualmente
curl -X POST http://localhost:8000/api/sitemap/test-scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"}'

# Ver logs
docker-compose -f docker-compose.prod.yml logs api | grep sitemap

# Verificar dependências instaladas
docker-compose -f docker-compose.prod.yml exec api pip list | grep -E "httpx|beautifulsoup4|lxml"
```

## 📚 Documentação

Documentos criados/atualizados:
- `DEPLOY_v1.0.7.md` - Este documento
- `SITEMAP_IMPORT.md` - Guia completo de importação
- `COMO_USAR_SITEMAP.md` - Exemplos práticos
- `GUIA_PROCESSAMENTO.md` - Explicação do processamento
- `ATUALIZACAO_DEPLOY.md` - Resumo das mudanças
- `COMANDOS_DEPLOY.md` - Comandos rápidos

## 🔗 Links Úteis

- **GitHub Actions:** https://github.com/sxconnect/catalog/actions
- **GHCR Packages:** https://github.com/orgs/sxconnect/packages
- **API Produção:** https://catalog-api.sxconnect.com.br
- **Frontend Produção:** https://catalog.sxconnect.com.br
- **API Docs:** https://catalog-api.sxconnect.com.br/docs

## 🎉 Conclusão

Deploy da versão 1.0.7 adiciona:
- Importação automática via sitemap XML
- Monitoramento em tempo real de processamento
- Interface visual melhorada
- Documentação completa

**Tempo estimado de deploy:** 10-15 minutos  
**Downtime:** ~30 segundos (durante restart)

---

**Versão:** v1.0.7 (Backend) + v1.0.3 (Frontend)  
**Data:** 2025  
**Autor:** SixPet Team
