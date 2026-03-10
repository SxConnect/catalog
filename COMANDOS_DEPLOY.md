# Comandos Rápidos de Deploy

## 🚀 Deploy Completo (Recomendado)

### Opção 1: Script Automático
```bash
# Dar permissão (primeira vez)
chmod +x release.sh

# Executar release
./release.sh 1.0.6 1.0.2

# Aguardar GitHub Actions completar
# Depois, no servidor:
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Opção 2: Manual
```bash
# 1. Commit e push
git add .
git commit -m "feat: add sitemap import and real-time monitoring"
git push origin main

# 2. Criar tags
git tag v1.0.6
git tag frontend-v1.0.2
git push origin v1.0.6
git push origin frontend-v1.0.2

# 3. Aguardar GitHub Actions
# Ver em: https://github.com/sxconnect/catalog/actions

# 4. No servidor
ssh usuario@servidor
cd /caminho/do/projeto
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 🔍 Verificar Status

### Verificar Builds no GitHub
```bash
# Abrir no navegador
https://github.com/sxconnect/catalog/actions
```

### Verificar Imagens no GHCR
```bash
# Abrir no navegador
https://github.com/orgs/sxconnect/packages

# Ou via CLI
docker pull ghcr.io/sxconnect/catalog:1.0.6
docker pull ghcr.io/sxconnect/catalog-frontend:1.0.2
```

### Verificar Serviços no Servidor
```bash
# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Logs específicos
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f frontend

# Health checks
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health
```

## 🧪 Testar Funcionalidades

### Testar API
```bash
# Stats
curl https://catalog-api.sxconnect.com.br/api/status/stats

# Preview sitemap
curl -X POST https://catalog-api.sxconnect.com.br/api/sitemap/preview \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 5
  }'

# Testar scraping
curl -X POST https://catalog-api.sxconnect.com.br/api/sitemap/test-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"
  }'
```

### Testar Frontend
```bash
# Abrir no navegador
https://catalog.sxconnect.com.br/dashboard/upload
https://catalog.sxconnect.com.br/dashboard/sitemap
```

## 🔄 Restart Serviços

### Restart Completo
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Restart Individual
```bash
docker-compose -f docker-compose.prod.yml restart api
docker-compose -f docker-compose.prod.yml restart worker
docker-compose -f docker-compose.prod.yml restart frontend
```

### Rebuild (se necessário)
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 🔙 Rollback

### Voltar para versão anterior
```bash
# 1. Editar docker-compose.prod.yml
# Mudar versões para:
#   api: ghcr.io/sxconnect/catalog:1.0.5
#   worker: ghcr.io/sxconnect/catalog:1.0.5
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.1

# 2. Aplicar
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 3. Verificar
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

## 🗄️ Backup

### Backup do Banco de Dados
```bash
# Backup
docker exec sixpet-catalog-postgres pg_dump -U sixpet sixpet_catalog > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore (se necessário)
docker exec -i sixpet-catalog-postgres psql -U sixpet sixpet_catalog < backup_20250101_120000.sql
```

### Backup dos Volumes
```bash
# Listar volumes
docker volume ls | grep sixpet

# Backup volume
docker run --rm -v catalog_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup.tar.gz /data
docker run --rm -v catalog_storage:/data -v $(pwd):/backup alpine tar czf /backup/storage_backup.tar.gz /data
```

## 📊 Monitoramento

### Ver Uso de Recursos
```bash
# CPU e Memória
docker stats

# Específico
docker stats sixpet-catalog-api sixpet-catalog-worker sixpet-catalog-frontend
```

### Ver Logs de Erro
```bash
# Últimos erros
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error

# Erros do worker
docker-compose -f docker-compose.prod.yml logs worker | grep -i error

# Erros da API
docker-compose -f docker-compose.prod.yml logs api | grep -i error
```

## 🧹 Limpeza

### Limpar Imagens Antigas
```bash
# Ver imagens
docker images | grep catalog

# Remover imagens antigas
docker image prune -a

# Remover imagens específicas
docker rmi ghcr.io/sxconnect/catalog:1.0.5
docker rmi ghcr.io/sxconnect/catalog-frontend:1.0.1
```

### Limpar Volumes Não Usados
```bash
# CUIDADO: Isso remove volumes não usados
docker volume prune
```

## 📝 Checklist Rápido

Deploy completo:
- [ ] Commit e push do código
- [ ] Criar tags (v1.0.6 e frontend-v1.0.2)
- [ ] Aguardar GitHub Actions
- [ ] Verificar imagens no GHCR
- [ ] Pull no servidor
- [ ] Up dos serviços
- [ ] Verificar logs
- [ ] Testar funcionalidades
- [ ] Backup do banco

## 🆘 Problemas Comuns

### GitHub Actions falhou
```bash
# Ver logs no GitHub
https://github.com/sxconnect/catalog/actions

# Tentar novamente
git push origin v1.0.6 --force
```

### Imagem não encontrada
```bash
# Verificar se existe
docker pull ghcr.io/sxconnect/catalog:1.0.6

# Se não existir, verificar GitHub Actions
# Pode precisar reautenticar no GHCR
```

### Serviço não inicia
```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs api

# Verificar variáveis de ambiente
docker-compose -f docker-compose.prod.yml config

# Restart
docker-compose -f docker-compose.prod.yml restart api
```

### Worker não processa
```bash
# Verificar se está rodando
docker-compose -f docker-compose.prod.yml ps worker

# Ver logs
docker-compose -f docker-compose.prod.yml logs worker

# Verificar Redis
docker-compose -f docker-compose.prod.yml logs redis

# Restart
docker-compose -f docker-compose.prod.yml restart worker redis
```

## 🔗 Links Úteis

- GitHub Actions: https://github.com/sxconnect/catalog/actions
- GHCR Packages: https://github.com/orgs/sxconnect/packages
- API Produção: https://catalog-api.sxconnect.com.br
- Frontend Produção: https://catalog.sxconnect.com.br
- Docs API: https://catalog-api.sxconnect.com.br/docs
