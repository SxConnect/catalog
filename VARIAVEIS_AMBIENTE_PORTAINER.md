# 🔧 CONFIGURAÇÃO DE VARIÁVEIS DE AMBIENTE - PORTAINER

## 🎯 PROBLEMA IDENTIFICADO

### Erro atual:
```
password authentication failed for user "sixpet"
```

### Causa:
- PostgreSQL existente no Portainer tem credenciais diferentes
- Variáveis de ambiente não estão configuradas corretamente
- Stack está usando valores padrão que não coincidem com o banco existente

## 📋 VARIÁVEIS NECESSÁRIAS NO PORTAINER

### 1. Acessar Configuração da Stack
```
Portainer → Stacks → catalog-stack → Editor
```

### 2. Configurar Variáveis de Ambiente
Na seção **Environment variables** da stack, adicionar:

```bash
# PostgreSQL Configuration
POSTGRES_USER=seu_usuario_postgres
POSTGRES_PASSWORD=sua_senha_postgres
POSTGRES_DB=seu_banco_postgres

# Redis Configuration (opcional - já funciona sem)
REDIS_URL=redis://redis:6379/0

# API Keys
GROQ_API_KEYS=sua_chave_groq

# MinIO/S3 Configuration (opcional)
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=sua_senha_minio
MINIO_S3_DOMAIN=mins3.sxconnect.com.br
S3_BUCKET=sixpet-catalog

# Admin Configuration
ADMIN_EMAIL=admin@sxconnect.com.br
ADMIN_PASSWORD=sua_senha_admin
NEXTAUTH_SECRET=sua_chave_secreta_nextauth
```

## 🔍 COMO DESCOBRIR AS CREDENCIAIS CORRETAS

### Opção 1: Verificar PostgreSQL Existente
```bash
# No Portainer, acessar o container PostgreSQL existente
# Ir em Containers → postgres → Console
# Executar:
psql -U postgres -l
```

### Opção 2: Verificar Logs do PostgreSQL
```bash
# No Portainer, acessar:
# Containers → postgres → Logs
# Procurar por mensagens de inicialização
```

### Opção 3: Usar Credenciais Padrão Comuns
Tente estas combinações:

```bash
# Opção A (padrão PostgreSQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

# Opção B (configuração atual)
POSTGRES_USER=sixpet
POSTGRES_PASSWORD=sixpet123
POSTGRES_DB=sixpet_catalog

# Opção C (admin genérico)
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin
POSTGRES_DB=catalog
```

## 🚀 PASSOS PARA CORREÇÃO

### 1. Identificar Credenciais
- Verificar PostgreSQL existente no Portainer
- Anotar usuário, senha e nome do banco

### 2. Configurar Variáveis
- Acessar Stack → Editor
- Adicionar variáveis na seção Environment
- Usar as credenciais corretas do PostgreSQL existente

### 3. Atualizar Stack
- Clicar em "Update the stack"
- Marcar "Re-pull image" 
- Aguardar containers reiniciarem

### 4. Verificar Logs
```bash
# Logs esperados (SUCESSO):
Database connected successfully
Redis connected successfully with URL: redis://redis:6379/0
Security configuration validation: OK (with Redis)
INFO: Application startup complete.
```

## 🎯 CONFIGURAÇÃO RECOMENDADA

### Para PostgreSQL Novo:
```yaml
environment:
  - POSTGRES_USER=sixpet
  - POSTGRES_PASSWORD=sixpet123
  - POSTGRES_DB=sixpet_catalog
  - DATABASE_URL=postgresql://sixpet:sixpet123@postgres:5432/sixpet_catalog
```

### Para PostgreSQL Existente:
```yaml
environment:
  - POSTGRES_USER=seu_usuario_existente
  - POSTGRES_PASSWORD=sua_senha_existente
  - POSTGRES_DB=seu_banco_existente
  - DATABASE_URL=postgresql://seu_usuario:sua_senha@postgres:5432/seu_banco
```

## ⚠️ IMPORTANTE

### Se PostgreSQL não existir:
- Portainer criará novo PostgreSQL com as credenciais configuradas
- Usar configuração recomendada acima

### Se PostgreSQL existir:
- **DEVE** usar as credenciais do PostgreSQL existente
- **NÃO** alterar credenciais do PostgreSQL existente
- Apenas ajustar variáveis da aplicação

## 🔧 ALTERNATIVA: RECRIAR BANCO

### Se quiser começar do zero:
1. Parar stack
2. Remover volume `postgres_data`
3. Configurar novas credenciais
4. Iniciar stack (criará novo PostgreSQL)

---

**Próximo passo**: Configurar variáveis corretas no Portainer e atualizar stack