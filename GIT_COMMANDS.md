# 📝 Comandos Git para Deploy

## 🚀 Enviar código para GitHub

Execute estes comandos na pasta `catalog/`:

```bash
# 1. Verificar status
git status

# 2. Adicionar todos os arquivos
git add .

# 3. Fazer commit
git commit -m "feat: add frontend application with Next.js 14"

# 4. Enviar para GitHub
git push origin main
```

## ✅ Verificar se enviou

Acesse: https://github.com/SxConnect/catalog

Você deve ver:
- Pasta `frontend/` com todo o código
- Arquivo `.github/workflows/docker-publish-frontend.yml`
- Arquivo `DEPLOY_GUIDE.md`

## 🔄 Acompanhar Build

Acesse: https://github.com/SxConnect/catalog/actions

Aguarde os workflows completarem:
- ✅ Build and Push Docker Image (backend)
- ✅ Build and Push Frontend Docker Image (frontend)

Tempo estimado: 5-7 minutos

## 🎯 Próximo Passo

Após o build completar, siga o guia: `DEPLOY_GUIDE.md`
