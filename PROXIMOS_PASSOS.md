# 🎯 PRÓXIMOS PASSOS - Deploy Frontend + Backend

## ✅ O que já foi feito

1. ✅ Backend completo desenvolvido e testado
2. ✅ Frontend completo com Next.js 14
3. ✅ Código do frontend copiado para `catalog/frontend/`
4. ✅ Docker Compose atualizado com serviço frontend
5. ✅ GitHub Actions configurado para build automático
6. ✅ Documentação completa criada

## 🚀 O que você precisa fazer AGORA

### Passo 1: Enviar código para GitHub (2 minutos)

```bash
cd catalog

git status
git add .
git commit -m "feat: add frontend application with Next.js 14"
git push origin main
```

### Passo 2: Aguardar build no GitHub Actions (5-7 minutos)

Acesse: https://github.com/SxConnect/catalog/actions

Aguarde os 2 workflows completarem:
- ✅ Build and Push Docker Image (backend)
- ✅ Build and Push Frontend Docker Image (frontend)

### Passo 3: Gerar NEXTAUTH_SECRET (30 segundos)

```bash
openssl rand -base64 32
```

Copie o resultado!

### Passo 4: Configurar variáveis no Portainer (2 minutos)

No Portainer, ao editar o stack `catalog`, adicione estas variáveis:

```bash
# PostgreSQL (já existentes)
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=9gkGSIXJ157Dbf
POSTGRES_DB=sixpet_catalog

# MinIO (já existentes)
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=lkasdl1fdkasmdk231eowd290dwop33
S3_BUCKET=sixpet-catalog

# Groq (já existente)
GROQ_API_KEYS=suas_chaves_aqui

# NOVAS - Frontend
NEXTAUTH_SECRET=cole_aqui_o_secret_gerado_no_passo_3
ADMIN_EMAIL=admin@sixpet.com
ADMIN_PASSWORD=SuaSenhaForte123!
```

### Passo 5: Atualizar stack no Portainer (1 minuto)

1. Portainer → Stacks → `catalog`
2. Clique em **Editor**
3. O docker-compose.prod.yml já está atualizado
4. Adicione as 3 novas variáveis (NEXTAUTH_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD)
5. Clique em **Update the stack**

### Passo 6: Verificar deployment (2 minutos)

```bash
# Ver containers
docker ps | grep sixpet-catalog

# Deve mostrar 5 containers:
# - sixpet-catalog-postgres
# - sixpet-catalog-redis
# - sixpet-catalog-api
# - sixpet-catalog-worker
# - sixpet-catalog-frontend (NOVO!)

# Testar endpoints
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health
```

### Passo 7: Acessar sistema (30 segundos)

Abra no navegador: https://catalog.sxconnect.com.br

Login:
- Email: admin@sixpet.com (ou o que você configurou)
- Senha: A que você configurou em ADMIN_PASSWORD

## 📚 Documentação Disponível

- `DEPLOY_GUIDE.md` - Guia completo de deploy passo a passo
- `GIT_COMMANDS.md` - Comandos Git para enviar código
- `check-deployment.sh` - Script de verificação automática
- `DEPLOY_FINAL.md` - Documentação técnica detalhada

## 🐛 Se algo der errado

Execute o script de verificação:

```bash
bash check-deployment.sh
```

Ou veja os logs:

```bash
docker logs -f sixpet-catalog-frontend
docker logs -f sixpet-catalog-api
```

## ⏱️ Tempo Total Estimado

- Passo 1: 2 min
- Passo 2: 5-7 min (aguardar build)
- Passo 3: 30 seg
- Passo 4: 2 min
- Passo 5: 1 min
- Passo 6: 2 min
- Passo 7: 30 seg

**Total: ~15 minutos**

## 🎉 Resultado Final

Após completar todos os passos, você terá:

✅ Frontend rodando em https://catalog.sxconnect.com.br
✅ Backend rodando em https://catalog-api.sxconnect.com.br
✅ Sistema completo com autenticação
✅ Tema dark/light funcionando
✅ Upload de PDF funcionando
✅ Dashboard com estatísticas
✅ Gerenciamento de API Keys
✅ Configurações de scraping e processamento

---

**COMECE AGORA**: Execute os comandos do Passo 1! 🚀
