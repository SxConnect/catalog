# ⚡ Comandos Rápidos

## 🚀 Deploy

```bash
# 1. Enviar para GitHub
cd catalog
git add .
git commit -m "feat: add frontend application"
git push origin main

# 2. Gerar NEXTAUTH_SECRET
openssl rand -base64 32

# 3. Aguardar build
# https://github.com/SxConnect/catalog/actions

# 4. Atualizar stack no Portainer
# Adicionar: NEXTAUTH_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD
```

## 🔍 Verificação

```bash
# Ver containers
docker ps | grep sixpet-catalog

# Verificar saúde
docker ps --format "table {{.Names}}\t{{.Status}}"

# Testar endpoints
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health

# Script completo
bash check-deployment.sh
```

## 📋 Logs

```bash
# Ver logs em tempo real
docker logs -f sixpet-catalog-frontend
docker logs -f sixpet-catalog-api
docker logs -f sixpet-catalog-worker

# Últimas 50 linhas
docker logs sixpet-catalog-frontend --tail 50
docker logs sixpet-catalog-api --tail 50
docker logs sixpet-catalog-worker --tail 50

# Todos os containers
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔄 Reiniciar

```bash
# Reiniciar um serviço
docker restart sixpet-catalog-frontend
docker restart sixpet-catalog-api
docker restart sixpet-catalog-worker

# Reiniciar todos
docker-compose -f docker-compose.prod.yml restart

# Recriar containers
docker-compose -f docker-compose.prod.yml up -d
```

## 🗄️ Banco de Dados

```bash
# Conectar ao PostgreSQL
docker exec -it sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog

# Listar tabelas
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "\dt"

# Ver produtos
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT COUNT(*) FROM products_catalog;"

# Ver catálogos
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "SELECT * FROM catalogs ORDER BY created_at DESC LIMIT 5;"

# Executar migrations
docker exec sixpet-catalog-api alembic upgrade head

# Ver migration atual
docker exec sixpet-catalog-api alembic current

# Histórico de migrations
docker exec sixpet-catalog-api alembic history
```

## 📮 Redis

```bash
# Conectar ao Redis
docker exec -it sixpet-catalog-redis redis-cli

# Ping
docker exec sixpet-catalog-redis redis-cli ping

# Ver chaves
docker exec sixpet-catalog-redis redis-cli keys "*"

# Ver info
docker exec sixpet-catalog-redis redis-cli info
```

## 🔧 Variáveis de Ambiente

```bash
# Ver variáveis da API
docker exec sixpet-catalog-api env | grep -E "DATABASE|REDIS|GROQ|S3"

# Ver variáveis do Frontend
docker exec sixpet-catalog-frontend env | grep -E "NEXT|ADMIN|AUTH"

# Ver variáveis do Worker
docker exec sixpet-catalog-worker env | grep -E "DATABASE|REDIS|GROQ"
```

## 🧹 Limpeza

```bash
# Remover containers parados
docker container prune -f

# Remover imagens não utilizadas
docker image prune -a -f

# Remover volumes não utilizados
docker volume prune -f

# Limpeza completa
docker system prune -a -f --volumes
```

## 📦 Atualizar

```bash
# Puxar novas imagens
docker pull ghcr.io/sxconnect/catalog:latest
docker pull ghcr.io/sxconnect/catalog-frontend:latest

# Recriar containers
docker-compose -f docker-compose.prod.yml up -d

# Ver versões
docker images | grep catalog
```

## 🐛 Debug

```bash
# Entrar no container
docker exec -it sixpet-catalog-api bash
docker exec -it sixpet-catalog-frontend sh

# Ver processos
docker top sixpet-catalog-api
docker top sixpet-catalog-worker

# Ver uso de recursos
docker stats sixpet-catalog-api sixpet-catalog-frontend sixpet-catalog-worker

# Inspecionar container
docker inspect sixpet-catalog-api
docker inspect sixpet-catalog-frontend

# Ver healthcheck
docker inspect sixpet-catalog-api | grep -A 20 Health
docker inspect sixpet-catalog-frontend | grep -A 20 Health
```

## 🌐 Testar API

```bash
# Health
curl https://catalog-api.sxconnect.com.br/health

# Docs
curl https://catalog-api.sxconnect.com.br/docs

# Listar produtos (precisa de API key)
curl -H "X-API-Key: sua_chave" https://catalog-api.sxconnect.com.br/api/products

# Buscar produtos
curl -H "X-API-Key: sua_chave" "https://catalog-api.sxconnect.com.br/api/search?q=ração"
```

## 📊 Monitoramento

```bash
# Ver uso de disco
df -h

# Ver uso de memória
free -h

# Ver processos Docker
docker ps -a

# Ver redes Docker
docker network ls

# Ver volumes Docker
docker volume ls

# Estatísticas em tempo real
docker stats
```

## 🔐 Segurança

```bash
# Ver portas expostas
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Ver redes
docker network inspect portainer_default

# Verificar SSL
curl -vI https://catalog.sxconnect.com.br 2>&1 | grep -i ssl

# Verificar certificado
openssl s_client -connect catalog.sxconnect.com.br:443 -servername catalog.sxconnect.com.br < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

## 📝 Backup

```bash
# Backup do banco
docker exec sixpet-catalog-postgres pg_dump -U sixpet sixpet_catalog > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup de volumes
docker run --rm -v sixpet-catalog_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup_$(date +%Y%m%d_%H%M%S).tar.gz /data

# Restaurar banco
cat backup.sql | docker exec -i sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog
```

## 🎯 URLs Úteis

- Frontend: https://catalog.sxconnect.com.br
- Backend: https://catalog-api.sxconnect.com.br
- Docs: https://catalog-api.sxconnect.com.br/docs
- GitHub: https://github.com/SxConnect/catalog
- Actions: https://github.com/SxConnect/catalog/actions
- MinIO: https://min.sxconnect.com.br
