# 🚀 Deploy v1.0.7 - COMANDOS PRONTOS

## ✅ O que foi implementado:
1. **Importação via Sitemap XML** - Extrai produtos de sites automaticamente
2. **Monitoramento em Tempo Real** - Veja progresso do processamento ao vivo
3. **Dockerfile atualizado** - Com dependências para web scraping

## 📋 COMANDOS PARA EXECUTAR AGORA

### 1️⃣ Fazer Release (Local)

```bash
# Dar permissão ao script (primeira vez)
chmod +x release.sh

# Executar release com versionamento
./release.sh 1.0.7 1.0.3
```

**O que o script faz:**
- ✅ Verifica se está no branch main
- ✅ Verifica mudanças não commitadas
- ✅ Cria tags: `v1.0.7` (backend) e `frontend-v1.0.3` (frontend)
- ✅ Faz push das tags
- ✅ GitHub Actions inicia build automaticamente

### 2️⃣ Aguardar GitHub Actions (2-5 minutos)

Acompanhe em: https://github.com/sxconnect/catalog/actions

**O que acontece:**
- 🔨 Build da imagem Docker do backend
- 🔨 Build da imagem Docker do frontend
- 📦 Push para GHCR:
  - `ghcr.io/sxconnect/catalog:1.0.7`
  - `ghcr.io/sxconnect/catalog:latest`
  - `ghcr.io/sxconnect/catalog-frontend:1.0.3`
  - `ghcr.io/sxconnect/catalog-frontend:latest`

### 3️⃣ Deploy no Servidor

```bash
# SSH no servidor
ssh usuario@servidor

# Ir para diretório do projeto
cd /caminho/do/projeto

# Pull das novas imagens
docker-compose -f docker-compose.prod.yml pull

# Restart dos serviços (downtime ~30 segundos)
docker-compose -f docker-compose.prod.yml up -d

# Verificar se subiu
docker-compose -f docker-compose.prod.yml ps

# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f
```

### 4️⃣ Verificar Funcionamento

```bash
# Health checks
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health

# Testar novo endpoint de stats
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

## 🧪 Testar no Frontend

### 1. Monitoramento de Upload
1. Acesse: https://catalog.sxconnect.com.br/dashboard/upload
2. Faça upload de um PDF
3. Veja a barra de progresso em tempo real
4. Aguarde conclusão

### 2. Importação via Sitemap
1. Acesse: https://catalog.sxconnect.com.br/dashboard/sitemap
2. Cole: `https://www.bbbpet.com.br/sitemap.xml`
3. Filtro: `/produto/`
4. Max: `10` produtos
5. Clique "Preview"
6. Clique "Testar" em uma URL
7. Clique "Importar Produtos"

## 📊 Versões

| Componente | Versão Anterior | Nova Versão |
|------------|----------------|-------------|
| Backend    | v1.0.6         | **v1.0.7**  |
| Frontend   | v1.0.2         | **v1.0.3**  |

## 🔄 Se algo der errado (Rollback)

```bash
# Editar docker-compose.prod.yml
nano docker-compose.prod.yml

# Voltar versões para:
#   api: ghcr.io/sxconnect/catalog:1.0.6
#   worker: ghcr.io/sxconnect/catalog:1.0.6
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.2

# Aplicar
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 📝 Checklist Rápido

- [ ] Executar `./release.sh 1.0.7 1.0.3`
- [ ] Aguardar GitHub Actions completar
- [ ] Verificar imagens no GHCR
- [ ] SSH no servidor
- [ ] `docker-compose pull`
- [ ] `docker-compose up -d`
- [ ] Verificar health checks
- [ ] Testar upload com monitoramento
- [ ] Testar importação via sitemap
- [ ] Verificar logs sem erros

## 🎯 Resumo do que mudou

**Você perguntou:**
> "Só ficar esperando? Por quanto tempo?"

**Agora você tem:**
- ✅ Barra de progresso em tempo real
- ✅ "Página 25 de 50 (50%)"
- ✅ "48 produtos encontrados"
- ✅ "Tempo estimado: 5m 30s"
- ✅ Notificação quando completa
- ✅ Histórico de uploads

**E mais:**
- ✅ Importação via sitemap XML
- ✅ Preview antes de importar
- ✅ Teste de extração individual
- ✅ Interface visual completa

## 📚 Documentação Completa

- `DEPLOY_v1.0.7.md` - Guia completo de deploy
- `GUIA_PROCESSAMENTO.md` - Explica o processamento
- `SITEMAP_IMPORT.md` - Como usar sitemap
- `COMO_USAR_SITEMAP.md` - Exemplos práticos
- `COMANDOS_DEPLOY.md` - Comandos rápidos

## 🆘 Problemas?

### GitHub Actions falhou
```bash
# Ver logs em: https://github.com/sxconnect/catalog/actions
# Recriar tag:
git tag -d v1.0.7
git push origin :refs/tags/v1.0.7
git tag v1.0.7
git push origin v1.0.7
```

### Serviço não sobe
```bash
# Ver logs
docker-compose -f docker-compose.prod.yml logs api
docker-compose -f docker-compose.prod.yml logs worker

# Restart forçado
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Worker não processa
```bash
# Verificar
docker-compose -f docker-compose.prod.yml logs worker
docker-compose -f docker-compose.prod.yml logs redis

# Restart
docker-compose -f docker-compose.prod.yml restart worker redis
```

## ⏱️ Tempo Estimado

- Release local: 1 minuto
- GitHub Actions: 2-5 minutos
- Deploy no servidor: 2 minutos
- Testes: 5 minutos
- **Total: ~10-15 minutos**

## 🎉 Pronto!

Após executar esses comandos, você terá:
- Monitoramento em tempo real funcionando
- Importação via sitemap disponível
- Sistema atualizado para v1.0.7

**Bom deploy! 🚀**
