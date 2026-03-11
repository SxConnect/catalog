# 🔧 Correção dos Erros de API no Frontend

## 🚨 Problema Identificado

O frontend estava apresentando erros de conexão (ERR_CONNECTION_REFUSED) ao tentar se comunicar com o backend. Os erros mostrados no console indicavam que:

1. A variável `NEXT_PUBLIC_API_URL` não estava sendo aplicada corretamente
2. O frontend estava tentando conectar em URLs incorretas
3. Faltava tratamento de erro e timeout nas requisições

## ✅ Correções Implementadas

### 1. **Dockerfile Corrigido**
- Adicionado suporte a `ARG NEXT_PUBLIC_API_URL` durante o build
- Variável de ambiente aplicada corretamente no momento do build

### 2. **Configuração da API Melhorada**
- Função `getApiUrl()` para detectar ambiente (servidor/cliente)
- URL padrão definida como `https://catalog-api.sxconnect.com.br`
- Timeout de 10 segundos adicionado
- Interceptor de erro para debug

### 3. **Endpoint de Debug**
- Criado `/api/debug` para verificar configurações
- Permite verificar se as variáveis estão sendo aplicadas

### 4. **Script de Teste**
- `test-connectivity.sh` para verificar conectividade
- Testa frontend, backend e conectividade interna

## 🚀 Como Aplicar as Correções na VPS

### **Passo 1: Aguardar Build**
Aguarde o GitHub Actions completar o build da nova imagem:
- https://github.com/SxConnect/catalog/actions

### **Passo 2: Atualizar na VPS**
```bash
# Baixar código atualizado
git pull origin main

# Executar atualização (vai puxar nova imagem)
./update-production.sh

# Testar conectividade
./test-connectivity.sh
```

### **Passo 3: Verificar Correção**
1. **Acessar o frontend**: https://catalog.sxconnect.com.br
2. **Verificar console**: Não deve mais ter erros de conexão
3. **Testar funcionalidades**: Dashboard deve carregar dados

### **Passo 4: Debug (se necessário)**
```bash
# Verificar configuração
curl https://catalog.sxconnect.com.br/api/debug

# Verificar logs
docker logs --tail 20 sixpet-catalog-frontend

# Verificar variáveis de ambiente
docker exec sixpet-catalog-frontend env | grep NEXT_PUBLIC
```

## 🔍 Verificações Pós-Correção

### **✅ Frontend deve mostrar:**
- Dashboard carregando sem erros
- Estatísticas aparecendo (Total de Produtos, etc.)
- Console sem erros de ERR_CONNECTION_REFUSED

### **✅ API Debug deve retornar:**
```json
{
  "NEXT_PUBLIC_API_URL": "https://catalog-api.sxconnect.com.br",
  "NODE_ENV": "production",
  "timestamp": "2026-03-11T...",
  "status": "ok"
}
```

### **✅ Logs do Frontend devem mostrar:**
- Sem erros de conexão
- Requisições sendo feitas para a URL correta
- Respostas do backend sendo recebidas

## 🛠️ Comandos Úteis

### **Verificar Status:**
```bash
# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Logs em tempo real
docker logs -f sixpet-catalog-frontend

# Testar APIs manualmente
curl https://catalog-api.sxconnect.com.br/health
curl https://catalog.sxconnect.com.br/api/health
```

### **Reiniciar se Necessário:**
```bash
# Reiniciar apenas o frontend
docker restart sixpet-catalog-frontend

# Ou rebuild completo
docker-compose -f docker-compose.prod.yml up -d --force-recreate frontend
```

## 📊 Resultado Esperado

Após aplicar as correções:

1. **✅ Dashboard carrega sem erros**
2. **✅ Estatísticas aparecem corretamente**
3. **✅ Console limpo (sem erros de conexão)**
4. **✅ Todas as funcionalidades operacionais**

## 🔄 Próximos Passos

1. **Aguardar build** no GitHub Actions
2. **Executar** `./update-production.sh` na VPS
3. **Testar** o frontend no navegador
4. **Verificar** se os erros foram resolvidos

---

**As correções foram implementadas e estão sendo buildadas. Execute a atualização na VPS assim que o build estiver completo!** 🚀