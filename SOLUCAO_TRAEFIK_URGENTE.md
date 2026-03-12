# 🚨 SOLUÇÃO URGENTE - TRAEFIK QUEBRADO

## PROBLEMA IDENTIFICADO
- **Traefik completamente quebrado** - todos os serviços retornando 404
- **Containers criados fora do Portainer** causaram conflitos
- **Credenciais PostgreSQL inconsistentes** corrigidas
- **MinIO, PAPI, Afiliados e outros serviços OFFLINE**

## ✅ CORREÇÕES JÁ APLICADAS
1. **Credenciais PostgreSQL corrigidas** para `9gkGSIXJ157Dbf`
2. **Novo subdomínio configurado**: `sixpetapi.sxconnect.com.br`
3. **Frontend atualizado** para usar novo subdomínio
4. **Scripts de correção criados**

## 🔧 PASSOS PARA RESOLVER (EXECUTE NA VPS)

### 1. Execute o script de correção
```bash
cd /root/dev-catalog
./fix-traefik-and-deploy.sh
```

### 2. Recrie a stack no Portainer
1. **Acesse Portainer**: https://portainer.sxconnect.com.br
2. **Delete stack existente** (se houver): `sixpet-catalog`
3. **Crie nova stack** com nome: `sixpet-catalog`
4. **Cole o conteúdo** do arquivo `docker-compose.prod.yml`
5. **Configure variáveis** (veja arquivo `portainer-env-vars.txt`):
   ```
   GROQ_API_KEYS=sua_chave_groq
   MINIO_ROOT_USER=admin
   MINIO_ROOT_PASSWORD=sua_senha_minio
   NEXTAUTH_SECRET=sua_secret_key_32_chars
   ADMIN_EMAIL=admin@sixpet.com
   ADMIN_PASSWORD=sua_senha_admin
   ```
6. **Deploy da stack**

### 3. Verifique se tudo funcionou
```bash
./verify-services.sh
```

## 🎯 RESULTADOS ESPERADOS
- ✅ **MinIO**: https://mins3.sxconnect.com.br
- ✅ **PAPI**: https://papi.sxconnect.com.br  
- ✅ **Portainer**: https://portainer.sxconnect.com.br
- ✅ **API Catálogo**: https://sixpetapi.sxconnect.com.br
- ✅ **Frontend Catálogo**: https://catalog.sxconnect.com.br

## ⚠️ REGRAS CRÍTICAS
1. **NUNCA MAIS** criar containers via CLI (`docker run`, `docker-compose up`)
2. **SEMPRE** usar Portainer para gerenciar containers
3. **Containers fora do Portainer** quebram o Traefik
4. **Usar apenas a rede** `portainer_default`

## 🔍 MONITORAMENTO
```bash
# Ver containers rodando
docker ps | grep -E "(traefik|sixpet-catalog)"

# Ver logs do Traefik
docker logs traefik --tail=20

# Monitoramento contínuo
watch -n 5 'docker ps | grep -E "(traefik|sixpet-catalog)"'
```

## 📋 CHECKLIST DE VERIFICAÇÃO
- [ ] Traefik rodando
- [ ] Containers problemáticos removidos
- [ ] Stack recriada no Portainer
- [ ] MinIO funcionando
- [ ] PAPI funcionando
- [ ] API Catálogo funcionando
- [ ] Frontend Catálogo funcionando

## 🆘 SE AINDA HOUVER PROBLEMAS
1. **Verificar logs do Traefik**: `docker logs traefik`
2. **Verificar redes**: `docker network ls`
3. **Reiniciar Traefik**: `cd /root/portainer && docker-compose restart traefik`
4. **Verificar DNS**: Confirmar se `sixpetapi.sxconnect.com.br` aponta para o servidor

---
**CRÍTICO**: Este problema afeta TODO o sistema de produção. Execute os passos imediatamente!