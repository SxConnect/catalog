# ⚠️ ORDEM CORRETA DE DEPLOY

## ❌ O que você fez (errado):
1. Tentou fazer pull da imagem v1.0.7
2. Mas a imagem ainda não existe no GHCR!

## ✅ ORDEM CORRETA:

### PASSO 1: Criar as tags e fazer push (LOCAL)
```bash
# No seu computador local, dentro da pasta catalog/

# 1. Commit das mudanças
git add .
git commit -m "feat: add sitemap import and real-time monitoring v1.0.7"

# 2. Push para o GitHub
git push origin main

# 3. Criar e push das tags
git tag v1.0.7
git tag frontend-v1.0.3
git push origin v1.0.7
git push origin frontend-v1.0.3
```

**OU use o script:**
```bash
chmod +x release.sh
./release.sh 1.0.7 1.0.3
```

### PASSO 2: Aguardar GitHub Actions (2-5 minutos)
Acesse: https://github.com/sxconnect/catalog/actions

Aguarde até ver:
- ✅ Build v1.0.7 - Success
- ✅ Build frontend-v1.0.3 - Success

### PASSO 3: Verificar se imagens existem no GHCR
```bash
# Tentar pull local para testar
docker pull ghcr.io/sxconnect/catalog:1.0.7
docker pull ghcr.io/sxconnect/catalog-frontend:1.0.3

# Se funcionar, as imagens existem!
```

### PASSO 4: Atualizar docker-compose.prod.yml
```yaml
services:
  api:
    image: ghcr.io/sxconnect/catalog:1.0.7  # ← Mudar aqui
  
  worker:
    image: ghcr.io/sxconnect/catalog:1.0.7  # ← Mudar aqui
  
  frontend:
    image: ghcr.io/sxconnect/catalog-frontend:1.0.3  # ← Mudar aqui
```

### PASSO 5: Deploy no servidor
```bash
ssh usuario@servidor
cd /caminho/do/projeto
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## 🔍 Por que deu erro?

Você tentou fazer pull da imagem `ghcr.io/sxconnect/catalog:1.0.7`, mas:
- ❌ A tag v1.0.7 ainda não foi criada no Git
- ❌ O GitHub Actions não rodou
- ❌ A imagem não foi buildada
- ❌ A imagem não existe no GHCR

## 🚀 SOLUÇÃO RÁPIDA AGORA:

### Opção A: Usar versão atual (v1.0.6)
```bash
# No servidor, o docker-compose.prod.yml já está correto (v1.0.6)
# Apenas fazer pull e restart
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

**Mas você NÃO terá as novas funcionalidades ainda!**

### Opção B: Fazer deploy correto da v1.0.7

#### 1. No seu computador local:
```bash
cd catalog

# Verificar se está tudo commitado
git status

# Se houver mudanças, commitar
git add .
git commit -m "feat: add sitemap import and real-time monitoring"

# Push
git push origin main

# Criar tags
git tag v1.0.7
git tag frontend-v1.0.3
git push origin v1.0.7
git push origin frontend-v1.0.3
```

#### 2. Aguardar GitHub Actions
Abra: https://github.com/sxconnect/catalog/actions

Aguarde até ver "✅ Success" nos dois workflows.

#### 3. Verificar imagens
```bash
# No seu computador ou servidor
docker pull ghcr.io/sxconnect/catalog:1.0.7
docker pull ghcr.io/sxconnect/catalog-frontend:1.0.3

# Se funcionar, pode continuar!
```

#### 4. Atualizar docker-compose.prod.yml
```bash
# Editar arquivo
nano docker-compose.prod.yml

# Mudar versões:
#   api: ghcr.io/sxconnect/catalog:1.0.7
#   worker: ghcr.io/sxconnect/catalog:1.0.7
#   frontend: ghcr.io/sxconnect/catalog-frontend:1.0.3

# Salvar e sair (Ctrl+X, Y, Enter)
```

#### 5. Deploy
```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f
```

## 📋 Checklist Correto

- [ ] **LOCAL:** Commit e push do código
- [ ] **LOCAL:** Criar tags (v1.0.7 e frontend-v1.0.3)
- [ ] **LOCAL:** Push das tags
- [ ] **GITHUB:** Aguardar Actions completar
- [ ] **GITHUB:** Verificar imagens no GHCR
- [ ] **SERVIDOR:** Atualizar docker-compose.prod.yml
- [ ] **SERVIDOR:** Pull das imagens
- [ ] **SERVIDOR:** Up dos serviços

## 🎯 Resumo

**Você pulou os passos 1-3!**

Precisa:
1. Criar as tags no Git (local)
2. Aguardar GitHub Actions buildar
3. Só depois fazer pull no servidor

## 💡 Dica

Use o script `release.sh` que faz tudo automaticamente:
```bash
./release.sh 1.0.7 1.0.3
```

Ele:
- ✅ Verifica se está tudo OK
- ✅ Cria as tags
- ✅ Faz push
- ✅ Mostra próximos passos

## 🔗 Links Úteis

- **GitHub Actions:** https://github.com/sxconnect/catalog/actions
- **GHCR Packages:** https://github.com/orgs/sxconnect/packages
- **Verificar imagem:** https://github.com/sxconnect/catalog/pkgs/container/catalog

---

**Agora você sabe a ordem correta! 🎓**
