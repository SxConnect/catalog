# Sistema de Extração da Cobasi

## Visão Geral

Sistema completo para extrair **TODOS os produtos da Cobasi** e salvar no banco de dados, rodando **em paralelo** com o processamento de catálogos PDF.

## Arquitetura

### 🔄 **Processamento Paralelo**
- **Worker PDF**: Continua processando catálogos normalmente
- **Worker Cobasi**: Novo worker que extrai produtos da Cobasi
- **Banco Unificado**: Ambos salvam no mesmo PostgreSQL

### 📊 **Tabela de Produtos Cobasi**
```sql
CREATE TABLE cobasi_products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(1000),
    brand VARCHAR(200),
    price DECIMAL(10,2),
    url VARCHAR(1000),
    
    -- Ficha técnica
    porte VARCHAR(200),           -- Raças Pequenas, Médias, Grandes
    tipo_racao VARCHAR(200),      -- Premium, Super Premium
    peso_racao VARCHAR(200),      -- 1kg, 3kg, 15kg, etc.
    sabor_racao VARCHAR(500),     -- Frango, Carne, Salmão
    idade VARCHAR(100),           -- Filhote, Adulto, Senior
    linha VARCHAR(200),           -- Choice, Special, etc.
    
    -- Dados nutricionais
    proteina_bruta VARCHAR(50),   -- 22g/kg
    fosforo VARCHAR(50),          -- 8000mg/kg
    calcio VARCHAR(50),           -- 9000mg/kg
    energia_metabolizavel VARCHAR(50), -- 3650kcal/kg
    
    -- Composição e descrição
    ingredientes TEXT,            -- Lista completa de ingredientes
    descricao TEXT,              -- Descrição do produto
    
    -- Metadados
    extracted_at TIMESTAMP,
    updated_at TIMESTAMP,
    raw_data JSONB               -- Dados completos em JSON
);
```

## Endpoints da API

### 🚀 **Iniciar Extração**
```bash
POST /api/cobasi/start-extraction
```
- Inicia extração em background
- Não interfere no processamento de PDFs
- Retorna task_id para acompanhamento

### 📊 **Status da Extração**
```bash
GET /api/cobasi/status
```
- Produtos extraídos hoje
- Total de produtos no banco
- Últimos produtos processados

### 🛍️ **Listar Produtos**
```bash
GET /api/cobasi/products?limit=20&brand=GranPlus&search=ração
```
- Lista produtos com filtros
- Busca por marca ou nome
- Paginação

### 📈 **Estatísticas**
```bash
GET /api/cobasi/stats
```
- Total de produtos e marcas
- Preços médios, mínimos e máximos
- Top marcas por quantidade
- Distribuição por tipo de ração

## Como Funciona

### 1. **Descoberta de Categorias**
```
https://www.cobasi.com.br/institucional/categorias
├── /c/cachorro
├── /c/cachorro/racao
├── /c/cachorro/racao/racao-seca
└── /c/gato/racao
```

### 2. **Extração de Produtos por Categoria**
- Acessa cada categoria
- Encontra links com padrão `/p?idsku=123456`
- Extrai lista de produtos

### 3. **Extração Detalhada de Cada Produto**
- Acessa página individual do produto
- Extrai informações das seções:
  - **Ficha Técnica**: Porte, tipo, peso, sabor, idade
  - **Detalhes do Produto**: Descrição, benefícios
  - **Composição**: Ingredientes completos
  - **Níveis de Garantia**: Proteína, fósforo, cálcio, etc.
  - **Vitaminas e Minerais**: Enriquecimento nutricional

### 4. **Salvamento Inteligente**
- Usa SKU como chave única
- Atualiza produtos existentes
- Mantém histórico de quando foi extraído

## Configuração e Deploy

### 1. **Variáveis de Ambiente**
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
CELERY_BROKER_URL=redis://redis:6379/0
```

### 2. **Iniciar Workers**
```bash
# Worker principal (PDFs + API)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Worker Celery (Cobasi + outras tarefas)
celery -A app.tasks.worker worker --loglevel=info
```

### 3. **Testar Localmente**
```bash
cd catalog
python test-cobasi-extraction.py
```

## Monitoramento

### 📊 **Logs**
- Arquivo: `cobasi_extraction.log`
- Formato: Timestamp, nível, mensagem
- Inclui estatísticas de progresso

### 🔍 **Métricas**
- Categorias processadas
- Produtos encontrados vs salvos
- Taxa de erro
- Tempo de processamento

### ⚠️ **Alertas**
- Taxa de erro > 10%
- Nenhum produto novo em 1 hora
- Falha de conexão com banco

## Estratégia de Extração

### 🎯 **Faseada**
1. **Fase 1**: 5 categorias principais (teste)
2. **Fase 2**: Todas as categorias de cachorro
3. **Fase 3**: Todas as categorias de gato
4. **Fase 4**: Demais categorias (pássaros, peixes, etc.)

### ⚡ **Performance**
- **Delay entre produtos**: 1 segundo
- **Delay entre categorias**: 2 segundos
- **Máximo concurrent**: 10 conexões
- **Timeout**: 30 segundos por requisição

### 🔄 **Atualização**
- **Frequência**: Diária (produtos novos)
- **Re-extração**: Semanal (atualizar preços)
- **Limpeza**: Mensal (remover produtos descontinuados)

## Integração com Sistema Atual

### ✅ **Compatibilidade Total**
- Não interfere no processamento de PDFs
- Usa mesma infraestrutura (PostgreSQL, Redis)
- Endpoints separados (`/api/cobasi/*`)

### 🔗 **Dados Unificados**
- Produtos da Cobasi ficam em tabela separada
- Podem ser consultados junto com produtos de catálogos
- Mesma estrutura de dados (nome, marca, preço, etc.)

### 📱 **Frontend**
- Nova seção "Produtos Cobasi" no admin
- Filtros por marca, tipo, porte
- Estatísticas em tempo real

## Próximos Passos

### 1. **Deploy Inicial**
```bash
# 1. Fazer commit das mudanças
git add .
git commit -m "feat: Sistema completo de extração da Cobasi"
git push origin main

# 2. Aguardar GitHub Actions fazer build
# 3. Atualizar VPS com novas imagens
# 4. Iniciar extração via API
```

### 2. **Teste de Produção**
```bash
# Iniciar extração
curl -X POST https://catalog-api.sxconnect.com.br/api/cobasi/start-extraction

# Verificar status
curl https://catalog-api.sxconnect.com.br/api/cobasi/status

# Ver produtos extraídos
curl "https://catalog-api.sxconnect.com.br/api/cobasi/products?limit=10"
```

### 3. **Monitoramento**
- Acompanhar logs de extração
- Verificar crescimento do banco de dados
- Ajustar delays se necessário

## Benefícios

### 🎯 **Para o Negócio**
- **Base completa** de produtos pet do Brasil
- **Dados estruturados** para análise e comparação
- **Atualização automática** de preços e disponibilidade

### 🔧 **Para o Sistema**
- **Escalabilidade**: Fácil adicionar outros sites
- **Robustez**: Tratamento de erros e retry
- **Performance**: Processamento assíncrono

### 📊 **Para Análise**
- **Inteligência de mercado**: Preços, marcas, tendências
- **Segmentação**: Por porte, idade, tipo de ração
- **Comparação**: Produtos similares de diferentes marcas