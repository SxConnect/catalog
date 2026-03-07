# 🚀 Quick Start - SixPet Catalog Engine

## Deploy Automático em 3 Passos

### 1️⃣ GitHub Actions (Automático)

O push para `main` já disparou o build! 

Verifique em: https://github.com/SxConnect/catalog/actions

A imagem será publicada em:
```
ghcr.io/sxconnect/catalog:latest
```

### 2️⃣ Preparar VPS

```bash
# SSH na VPS
ssh user@seu-servidor.com

# Criar diretório
mkdir -p /opt/sixpet-catalog
cd /opt/sixpet-catalog

# Baixar arquivos
curl -O https://raw.githubusercontent.com/SxConnect/catalog/main/docker-compose.prod.yml
curl -O https://raw.githubusercontent.com/SxConnect/catalog/main/.env.prod.example

# Configurar
cp .env.prod.example .env
nano .env  # Editar com suas credenciais
```

### 3️⃣ Deploy via Portainer

**Opção A: Via UI**
1. Portainer > Stacks > Add Stack
2. Nome: `sixpet-catalog`
3. Upload: `docker-compose.prod.yml`
4. Environment: Cole `.env`
5. Deploy!

**Opção B: Via CLI**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ✅ Verificar

```bash
# Containers rodando
docker ps | grep sixpet-catalog

# Health check
curl https://catalog-api.sxconnect.com.br/health

# Logs
docker logs sixpet-catalog-api -f
```

## 🌐 URLs

- **API:** https://catalog-api.sxconnect.com.br
- **Docs:** https://catalog-api.sxconnect.com.br/docs
- **MinIO:** https://minio.catalog.sxconnect.com.br

## 📚 Documentação Completa

Ver: [DEPLOY.md](DEPLOY.md)

## 🎯 Pronto!

Seu sistema está no ar e pronto para processar catálogos! 🎉
