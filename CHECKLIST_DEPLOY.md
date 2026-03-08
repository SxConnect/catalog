# ✅ Checklist de Deploy - SixPet Catalog

Use este checklist para garantir que todos os passos foram executados corretamente.

## 📋 Pré-Deploy

- [ ] Código do frontend copiado para `catalog/frontend/` ✅ (já feito)
- [ ] Docker Compose atualizado com serviço frontend ✅ (já feito)
- [ ] GitHub Actions configurado ✅ (já feito)
- [ ] Documentação criada ✅ (já feito)

## 🚀 Deploy

### Passo 1: Git Push
- [ ] Executei `git status` e vi os arquivos novos
- [ ] Executei `git add .`
- [ ] Executei `git commit -m "feat: add frontend application"`
- [ ] Executei `git push origin main`
- [ ] Código apareceu no GitHub

### Passo 2: GitHub Actions
- [ ] Acessei https://github.com/SxConnect/catalog/actions
- [ ] Workflow "Build and Push Docker Image" completou ✅
- [ ] Workflow "Build and Push Frontend Docker Image" completou ✅
- [ ] Imagens publicadas no GitHub Container Registry

### Passo 3: Gerar Secrets
- [ ] Executei `openssl rand -base64 32`
- [ ] Copiei o NEXTAUTH_SECRET gerado
- [ ] Defini ADMIN_EMAIL
- [ ] Defini ADMIN_PASSWORD

### Passo 4: Configurar Portainer
- [ ] Acessei Portainer
- [ ] Fui em Stacks → catalog
- [ ] Adicionei variável `NEXTAUTH_SECRET`
- [ ] Adicionei variável `ADMIN_EMAIL`
- [ ] Adicionei variável `ADMIN_PASSWORD`
- [ ] Cliquei em "Update the stack"

### Passo 5: Verificar Containers
- [ ] Executei `docker ps | grep sixpet-catalog`
- [ ] Container `sixpet-catalog-postgres` está rodando (healthy)
- [ ] Container `sixpet-catalog-redis` está rodando (healthy)
- [ ] Container `sixpet-catalog-api` está rodando (healthy)
- [ ] Container `sixpet-catalog-worker` está rodando
- [ ] Container `sixpet-catalog-frontend` está rodando (healthy) ⭐ NOVO

### Passo 6: Executar Migrations
- [ ] Executei `docker exec sixpet-catalog-api alembic upgrade head`
- [ ] Migrations aplicadas com sucesso
- [ ] Tabelas criadas no banco

### Passo 7: Testar Endpoints
- [ ] Backend: `curl https://catalog-api.sxconnect.com.br/health` retorna 200
- [ ] Frontend: `curl https://catalog.sxconnect.com.br/api/health` retorna 200
- [ ] Backend docs acessível: https://catalog-api.sxconnect.com.br/docs

### Passo 8: Acessar Frontend
- [ ] Acessei https://catalog.sxconnect.com.br
- [ ] Página de login carregou
- [ ] Fiz login com ADMIN_EMAIL e ADMIN_PASSWORD
- [ ] Dashboard carregou corretamente
- [ ] Menu lateral funcionando

### Passo 9: Testar Funcionalidades
- [ ] Tema dark/light funcionando (botão no header)
- [ ] Navegação entre páginas funcionando
- [ ] Página de Upload acessível
- [ ] Página de API Keys acessível
- [ ] Página de Configurações acessível

### Passo 10: Configuração Inicial
- [ ] Adicionei pelo menos 1 API Key Groq
- [ ] Configurei Web Scraping (extrações/segundo)
- [ ] Configurei Processamento (catálogos simultâneos)
- [ ] Salvei as configurações

### Passo 11: Teste de Upload
- [ ] Fui em Upload
- [ ] Arrastei um PDF de teste
- [ ] Marquei os campos para enriquecimento
- [ ] Cliquei em "Enviar Catálogo"
- [ ] Processamento iniciou
- [ ] Acompanhei no Dashboard

## 🎯 Verificação Final

### Containers
```bash
docker ps | grep sixpet-catalog
```
Deve mostrar 5 containers rodando:
- [ ] sixpet-catalog-postgres (healthy)
- [ ] sixpet-catalog-redis (healthy)
- [ ] sixpet-catalog-api (healthy)
- [ ] sixpet-catalog-worker (running)
- [ ] sixpet-catalog-frontend (healthy)

### Endpoints
```bash
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health
```
Ambos devem retornar 200:
- [ ] Backend health: 200 OK
- [ ] Frontend health: 200 OK

### Banco de Dados
```bash
docker exec sixpet-catalog-postgres psql -U sixpet -d sixpet_catalog -c "\dt"
```
Deve mostrar as tabelas:
- [ ] ai_api_keys
- [ ] alembic_version
- [ ] catalogs
- [ ] products_catalog
- [ ] settings

### Logs
```bash
docker logs sixpet-catalog-frontend --tail 10
docker logs sixpet-catalog-api --tail 10
```
Não deve ter erros críticos:
- [ ] Frontend sem erros
- [ ] Backend sem erros

## 📊 Status Final

### ✅ Sistema Completo
- [ ] Backend rodando
- [ ] Frontend rodando
- [ ] Banco de dados configurado
- [ ] Migrations aplicadas
- [ ] Autenticação funcionando
- [ ] Tema dark/light funcionando
- [ ] Upload funcionando
- [ ] API Keys configuradas
- [ ] Configurações salvas
- [ ] Teste de upload realizado

## 🎉 Pronto!

Se todos os itens acima estão marcados, seu sistema está 100% operacional!

**URLs**:
- 🌐 Frontend: https://catalog.sxconnect.com.br
- 🔌 Backend: https://catalog-api.sxconnect.com.br
- 📚 Docs: https://catalog-api.sxconnect.com.br/docs

**Próximos Passos**:
1. Fazer upload dos catálogos reais
2. Monitorar processamento
3. Verificar produtos extraídos
4. Ajustar configurações conforme necessário

## 🐛 Se algo não funcionou

Execute o script de verificação:
```bash
bash check-deployment.sh
```

Ou consulte:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
- [COMANDOS_RAPIDOS.md](COMANDOS_RAPIDOS.md)

---

**Tempo total estimado**: 15-20 minutos
**Dificuldade**: Fácil (seguindo o passo a passo)
