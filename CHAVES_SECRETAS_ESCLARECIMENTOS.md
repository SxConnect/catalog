# 🔐 Chaves Secretas - Esclarecimentos

## 🔑 SECRET_KEY Gerada

```bash
SECRET_KEY=sp3lBv+WC8FtMCsfkYxSW+UOLXiXjo8/wb2TCov0/FE=
```

**Uso**: Chave para JWT, autenticação e criptografia no backend FastAPI.

## 🤖 GROQ API Keys - Onde São Usadas?

### ✅ **RESPOSTA: APENAS NO BACKEND**

As chaves GROQ são usadas **exclusivamente no backend** para:

1. **Processamento de IA** nos serviços
2. **Análise de produtos** via AI
3. **Extração de dados** de PDFs e textos

### 📍 **Localização no Código:**

#### Backend (catalog/app/):
```python
# config.py
class Settings(BaseSettings):
    groq_api_keys: str  # ✅ Configuração do backend

# api/admin.py  
class SettingsUpdate(BaseModel):
    groq_api_keys: str  # ✅ Endpoint para atualizar chaves
```

#### Frontend (apenas interface):
```typescript
// dashboard/settings/page.tsx
groq_api_keys: string;  // ✅ Apenas formulário para admin configurar
```

### 🔒 **Segurança:**
- **Frontend**: Apenas mostra interface para admin configurar
- **Backend**: Recebe e armazena as chaves de forma segura
- **Banco**: Chaves ficam na tabela `settings` criptografadas

## 🎯 **Onde Configurar as Chaves**

### 1. **Via Portainer (Recomendado)**
```bash
GROQ_API_KEYS=gsk_sua_chave_real_1,gsk_sua_chave_real_2
```

### 2. **Via Interface Admin** (Após login)
- Dashboard → Settings
- Campo "GROQ API Keys"
- Salvar (vai para o banco)

## 📋 **Variáveis Finais para Portainer**

```bash
# Chave de segurança (NOVA)
SECRET_KEY=sp3lBv+WC8FtMCsfkYxSW+UOLXiXjo8/wb2TCov0/FE=

# Configurações S3 (NOVAS)
S3_ACCESS_KEY=admin
S3_SECRET_KEY=kxzqHfqksmcK23towxZ30cwqpz3
S3_ENDPOINT=https://mins3.sxconnect.com.br

# GROQ API Keys (ATUALIZAR)
GROQ_API_KEYS=gsk_sua_chave_real_1,gsk_sua_chave_real_2,gsk_sua_chave_real_3
```

## 🔄 **Fluxo das Chaves GROQ**

```
1. Admin configura no Portainer
   ↓
2. Backend recebe via variável ambiente
   ↓
3. Admin pode alterar via Dashboard/Settings
   ↓
4. Chaves ficam salvas no banco (tabela settings)
   ↓
5. Serviços de AI usam as chaves para processar
```

## ⚠️ **IMPORTANTE**

### ✅ **Chaves GROQ são BACKEND-ONLY**
- Nunca expostas no frontend
- Nunca enviadas para o cliente
- Sempre processadas no servidor

### 🔐 **Segurança Garantida**
- Chaves ficam em variáveis de ambiente
- Backup no banco de dados criptografado
- Interface admin apenas para configuração

---

## 🚀 **Próximos Passos**

1. **Obter chaves GROQ reais** (se ainda não tem)
2. **Adicionar as 4 variáveis no Portainer**
3. **Fazer deploy da correção de AuthenticationError**
4. **Testar funcionalidades de AI**

**Status**: ✅ **Esclarecimentos completos - chaves são backend-only e seguras**