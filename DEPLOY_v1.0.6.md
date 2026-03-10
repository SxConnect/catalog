# Deploy v1.0.6 - Sitemap Import + Real-time Monitoring

## 🎯 Novidades desta Versão

### Backend (catalog v1.0.6)
- ✅ Importação via Sitemap XML
- ✅ API de monitoramento em tempo real
- ✅ Endpoints de status de processamento
- ✅ Dependências para web scraping (httpx, beautifulsoup4, lxml)

### Frontend (catalog-frontend v1.0.2)
- ✅ Interface de importação via sitemap
- ✅ Monitoramento em tempo real de uploads
- ✅ Barra de progresso com estimativa de tempo
- ✅ Histórico de uploads recentes
- ✅ Link no menu para importação via sitemap

## 📋 Processo de Deploy

### 1. Criar Tags no Git

```bash
# Backend - v1.0.6
cd catalog
git add .
git commit -m "feat: add sitemap import and real-time monitoring"
git tag v1.0.6
git push origin main
git push origin v1.0.6

# Frontend - v1.0.2
cd ../catalog-frontend
git add .
git commit -m "feat: add sitemap import UI and real-time upload monitoring"
git tag v1.0.2
git push origin main
git push origin v1.0.2
```

### 2. GitHub Actions Automático

Após push das tags, o GitHub Actions irá:
- ✅ Build das imagens Docker
- ✅ Push para GHCR com tags:
  - `ghcr.io/sxconnect/catalog:1.0.6`
  - `ghcr.io/sxconnect/catalog:latest`
  - `ghcr.io/sxconnect/catalog-frontend:1.0.2`
  - `ghcr.io/sxconnect/catalog-frontend:latest`

Acompanhe em: https://github.com/sxconnect/catalog/actions

### 3. Atualizar docker-compose.prod.yml

```yaml
services:
  api:
    image: ghcr.io/sxconnect/catalog:1.0.6  # ← Atualizar aqui
    # ... resto da config

  worker:
    image: ghcr.io/sxconnect/catalog:1.0.6  # ← Atualizar aqui
    # ... resto da config

  frontend:
    image: ghcr.io/sxconnect/catalog-frontend:1.0.2  # ← Atualizar aqui
    # ... resto da config
```

### 4. Deploy no Servidor

```bash
# SSH no servidor
ssh usuario@servidor

# Ir para diretório do projeto
cd /caminho/do/projeto

# Pull das novas imagens
docker-compose -f docker-compose.prod.yml pull

# Restart dos serviços
docker-compose -f docker-compose.prod.yml up -d

# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### 5. Verificar Funcionamento

```bash
# Health checks
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health

# Testar novos endpoints
curl https://catalog-api.sxconnect.com.br/api/status/stats

# Testar sitemap (preview)
curl -X POST https://catalog-api.sxconnect.com.br/api/sitemap/preview \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 5
  }'
```

## 🧪 Testes Pós-Deploy

### 1. Testar Upload com Monitoramento
1. Acesse: https://catalog.sxconnect.com.br/dashboard/upload
2. Faça upload de um PDF pequeno (5-10 páginas)
3. Verifique se aparece:
   - ✅ Barra de progresso
   - ✅ Páginas processadas
   - ✅ Produtos encontrados
   - ✅ Tempo estimado
4. Aguarde conclusão
5. Verifique mensagem de sucesso

### 2. Testar Importação via Sitemap
1. Acesse: https://catalog.sxconnect.com.br/dashboard/sitemap
2. Cole URL: `https://www.bbbpet.com.br/sitemap.xml`
3. Filtro: `/produto/`
4. Max produtos: `10`
5. Clique "Preview"
6. Verifique se mostra URLs
7. Clique "Testar" em uma URL
8. Verifique dados extraídos
9. Clique "Importar Produtos"
10. Verifique sucesso

### 3. Verificar Logs
```bash
# Verificar se não há erros
docker-compose -f docker-compose.prod.yml logs --tail=100 api
docker-compose -f docker-compose.prod.yml logs --tail=100 worker
docker-compose -f docker-compose.prod.yml logs --tail=100 frontend

# Verificar se worker está processando
docker-compose -f docker-compose.prod.yml logs -f worker
```

## 🔄 Rollback (se necessário)

Se algo der errado, voltar para versão anterior:

```bash
# Editar docker-compose.prod.yml
# Mudar de volta para:
#   api: ghcr.io/sxconnect/catalog:1.0.5
#   worker: ghcr.io/sxconnect/catalog:1.0.5
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.1

# Aplicar
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Novos Endpoints da API

### Status de Catálogo
```bash
GET /api/status/catalog/{id}/status
```
Retorna status detalhado do processamento.

### Produtos de Catálogo
```bash
GET /api/status/catalog/{id}/products
```
Lista produtos extraídos de um catálogo.

### Catálogos Recentes
```bash
GET /api/status/recent?limit=10
```
Lista últimos catálogos processados.

### Estatísticas
```bash
GET /api/status/stats
```
Estatísticas gerais do sistema.

### Preview Sitemap
```bash
POST /api/sitemap/preview
{
  "sitemap_url": "https://exemplo.com/sitemap.xml",
  "url_filter": "/produto/",
  "max_urls": 10
}
```

### Testar Scraping
```bash
POST /api/sitemap/test-scrape
{
  "url": "https://exemplo.com/produto/123"
}
```

### Importar Sitemap
```bash
POST /api/sitemap/import
{
  "sitemap_url": "https://exemplo.com/sitemap.xml",
  "catalog_id": 1,
  "url_filter": "/produto/",
  "max_products": 50,
  "auto_save": true
}
```

## 📝 Notas Importantes

### Dependências Novas
O Dockerfile foi atualizado com:
- `libxml2-dev` e `libxslt-dev` (parsing XML)
- `httpx` (requisições HTTP assíncronas)
- `beautifulsoup4` e `lxml` (web scraping)

### Performance
- Sitemap processa 10 URLs por vez
- Delay de 1 segundo entre lotes
- Timeout de 30 segundos por requisição

### Limites Recomendados
- Sitemap: 50-100 produtos por importação
- Teste primeiro com 10-20 produtos

## 🎉 Checklist Final

Antes de considerar deploy completo:

- [ ] Tags criadas e pushed (v1.0.6 e v1.0.2)
- [ ] GitHub Actions completou builds
- [ ] Imagens disponíveis no GHCR
- [ ] docker-compose.prod.yml atualizado
- [ ] Pull das novas imagens no servidor
- [ ] Serviços reiniciados
- [ ] Health checks passando
- [ ] Upload com monitoramento funcionando
- [ ] Importação via sitemap funcionando
- [ ] Logs sem erros críticos
- [ ] Backup do banco de dados feito

## 📚 Documentação

Documentos criados nesta versão:
- `SITEMAP_IMPORT.md` - Guia completo de importação
- `COMO_USAR_SITEMAP.md` - Exemplos práticos
- `GUIA_PROCESSAMENTO.md` - Explicação do processamento
- `DEPLOY_v1.0.6.md` - Este documento

## 🚀 Próxima Versão (v1.0.7)

Sugestões para próxima release:
- Webhook de notificação quando processamento terminar
- Upload múltiplo de PDFs
- Agendamento de importação via sitemap
- Cache de scraping
- Validação avançada de dados

---

**Versão:** 1.0.6 (Backend) + 1.0.2 (Frontend)  
**Data:** 2025  
**Autor:** SixPet Team
