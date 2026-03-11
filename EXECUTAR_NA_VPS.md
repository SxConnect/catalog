# 🚀 EXECUTAR NA VPS - Correção de Problemas de Rede

## ⚡ **PASSOS IMEDIATOS - Execute na VPS:**

### **Passo 1: Fazer Pull do Código Atualizado**
```bash
cd /caminho/do/projeto  # Vá para o diretório do projeto
git pull origin main
```

### **Passo 2: Aplicar Correção de Emergência**
```bash
# Tornar o script executável (se necessário)
chmod +x fix-network-emergency.sh

# Executar correção de emergência
./fix-network-emergency.sh
```

### **Passo 3: Aguardar e Verificar**
O script vai:
- ⏳ Parar containers (30 segundos)
- 🗑️ Remover containers problemáticos
- 📥 Baixar imagens atualizadas
- 🔄 Recriar containers
- ⏳ Aguardar 20 segundos
- 🗄️ Executar migrações
- 🔍 Testar conectividade

### **Passo 4: Testar o Sistema**
Após o script terminar:

1. **Abrir o frontend**: https://catalog.sxconnect.com.br
2. **Verificar console**: F12 → Console (deve estar limpo)
3. **Testar dashboard**: Estatísticas devem aparecer
4. **Testar backend**: https://catalog-api.sxconnect.com.br/health

---

## 🔍 **Se Ainda Houver Problemas:**

### **Verificar Logs:**
```bash
# Logs do frontend
docker logs --tail 20 sixpet-catalog-frontend

# Logs do backend
docker logs --tail 20 sixpet-catalog-api

# Status dos containers
docker-compose -f docker-compose.prod.yml ps
```

### **Teste Manual de Conectividade:**
```bash
# Testar backend
curl https://catalog-api.sxconnect.com.br/health

# Testar frontend
curl https://catalog.sxconnect.com.br/api/health

# Testar conectividade interna
docker exec sixpet-catalog-frontend curl -f http://api:8000/health
```

---

## 📊 **Resultado Esperado:**

### **✅ Sucesso - Você deve ver:**
- Dashboard carregando sem erros
- Console limpo (sem erros vermelhos)
- Estatísticas aparecendo:
  - Total de Produtos: X
  - Catálogos Processados: X
  - Taxa de Sucesso: X%
  - Última Atualização: Hoje

### **❌ Se ainda houver problemas:**
- Execute: `./test-connectivity.sh`
- Verifique logs: `docker logs -f sixpet-catalog-frontend`
- Reinicie containers: `docker restart sixpet-catalog-frontend`

---

## 🆘 **Comandos de Emergência:**

### **Reiniciar Tudo:**
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### **Rebuild Completo:**
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

### **Verificar Rede:**
```bash
docker network ls
docker network inspect portainer_default
```

---

## 📞 **Status Report:**

Após executar, reporte:

1. **✅/❌ Script executou sem erros?**
2. **✅/❌ Frontend carrega sem erros no console?**
3. **✅/❌ Dashboard mostra estatísticas?**
4. **✅/❌ Backend responde em /health?**

---

**EXECUTE AGORA E REPORTE O RESULTADO!** 🎯