# Sistema de Extração da Cobasi

## Visão Geral

Sistema completo para extrair **TODOS os produtos da Cobasi** e salvar no banco de dados, rodando **em paralelo** com o processamento de catálogos PDF. **ATUALIZADO** para usar sistema de deduplicação unificado.

## Arquitetura

### 🔄 **Processamento Paralelo**
- **Worker PDF**: Continua processando catálogos normalmente
- **Worker Cobasi**: Novo worker que extrai produtos da Cobasi
- **Banco Unificado**: Ambos salvam na mesma tabela `unified_products`

### 📊 **Tabela Unificada de Produtos**
```sql
CREATE TABLE unified_products (
    id SERIAL PRIMARY KEY,
    
    -- Identificadores únicos
    sku VARCHAR(100),
    ean VARCHAR(50),
    name_normalized VARCHAR(500), -- Nome normalizado para busca
    
    -- Informações básicas
    name VARCHAR(1000) NOT NULL,
    brand VARCHAR(200),
    price DECIMAL(10,2),
    original_price DECIMAL(10,2),
    
    -- URLs e imagens
    source_url VARCHAR(1000),
    images TEXT[], -- Array de URLs de imagens
    
    -- Ficha técnica (dados ricos da Cobasi/web)
    porte VARCHAR(200),           -- Raças Pequenas, Médias, Grandes
    tipo_produto VARCHAR(200),    -- Ração Seca, Ração Úmida, Petisco
    peso_produto VARCHAR(200),    -- 1kg, 3kg, 15kg, etc.
    sabor VARCHAR(500),          -- Frango, Carne, Salmão
    idade_pet VARCHAR(100),      -- Filhote, Adulto, Senior
    linha_produto VARCHAR(200),   -- Choice, Special, Premium
    
    -- Dados nutricionais detalhados
    proteina_bruta VARCHAR(50),
    fosforo VARCHAR(50),
    calcio_min VARCHAR(50),
    energia_metabolizavel VARCHAR(50),
    
    -- Composição e ingredientes
    ingredientes_principais TEXT,
    composicao_completa TEXT,
    
    -- Descrição e marketing
    descricao_curta TEXT,
    descricao_completa TEXT,
    beneficios TEXT[],
    
    -- Origem dos dados
    source_type VARCHAR(50) NOT NULL, -- 'cobasi', 'catalog', 'web_enriched'
    source_id VARCHAR(100),           -- ID do catálogo ou site de origem
    catalog_id INTEGER,               -- Referência ao catálogo se veio de PDF
    
    -- Enriquecimento
    is_enriched BOOLEAN DEFAULT FALSE,
    enriched_at TIMESTAMP WITH TIME ZONE,
    enrichment_source VARCHAR(200),
    
    -- Metadados
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Dados brutos para análise
    raw_data JSONB,
    
    -- Constraints
    UNIQUE(sku, source_type) -- Permite mesmo SKU de fontes diferentes
);
```

## Sistema de Deduplicação

### 🔍 **Detecção Inteligente**
- **Busca por SKU**: Prioridade máxima para produtos com SKU
- **Similaridade de nomes**: Algoritmo de matching com 85% de threshold
- **Normalização**: Remove acentos, caracteres especiais, palavras comuns
- **Verificação cruzada**: Compara produtos de diferentes fontes

### 🔄 **Fluxo de Processamento**

#### **Produtos da Cobasi**
1. Extrai dados completos da página do produto
2. Verifica duplicatas na tabela unificada
3. Se existe: atualiza dados se mais completos
4. Se não existe: salva como novo produto

#### **Produtos de Catálogos**
1. Extrai dados básicos do PDF
2. Verifica se já existe produto similar (Cobasi/outros)
3. Se existe: apenas associa ao catálogo, não reprocessa
4. Se não existe: enriquece com dados web e salva

## Endpoints da API

### 🚀 **Extração da Cobasi**
```bash
# Iniciar extração
POST /api/cobasi/start-extraction

# Status da extração
GET /api/cobasi/status

# Listar produtos da Cobasi
GET /api/cobasi/products?limit=20&brand=GranPlus

# Estatísticas da Cobasi
GET /api/cobasi/stats
```

### 📊 **Sistema Unificado**
```bash
# Status geral do sistema
GET /api/unified/status

# Buscar em todas as fontes
GET /api/unified/search?query=ração+frango&source=cobasi

# Encontrar duplicatas
GET /api/unified/duplicates?threshold=0.85
```

### 📁 **Catálogos (Integrado)**
```bash
# Upload continua igual
POST /api/catalog/upload

# Status mostra produtos unificados
GET /api/catalog/{id}/status
```

## Fluxo de Dados

### 1. **Extração da Cobasi**
```
Cobasi Worker → Produtos Ricos → Tabela Unificada
                                      ↓
                               Sistema de Deduplicação
```

### 2. **Processamento de Catálogos**
```
PDF → AI Extraction → Verificar Duplicatas → Enriquecer Web → Tabela Unificada
                           ↓                      ↓
                    Se existe: associar    Se não existe: salvar
```

### 3. **Consulta Unificada**
```
API Endpoints → Tabela Unificada → Produtos de Todas as Fontes
```

## Configuração e Deploy

### 1. **Variáveis de Ambiente**
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
CELERY_BROKER_URL=redis://redis:6379/0
```

### 2. **Iniciar Sistema**
```bash
# API principal
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Worker Celery (Cobasi + PDFs)
celery -A app.tasks.worker worker --loglevel=info
```

### 3. **Testar Sistema**
```bash
# Verificar status geral
curl https://catalog-api.sxconnect.com.br/api/unified/status

# Iniciar extração da Cobasi
curl -X POST https://catalog-api.sxconnect.com.br/api/cobasi/start-extraction

# Buscar produtos
curl "https://catalog-api.sxconnect.com.br/api/unified/search?query=ração"
```

## Benefícios da Integração

### ✅ **Para Produtos de Catálogos**
- **Não duplica** produtos já extraídos da Cobasi
- **Enriquece automaticamente** com dados web se não existir
- **Associa corretamente** produtos existentes aos catálogos

### ✅ **Para Produtos da Cobasi**
- **Dados completos** extraídos diretamente da fonte
- **Ficha técnica rica** com informações nutricionais
- **Atualização automática** de preços e disponibilidade

### ✅ **Para o Sistema**
- **Base unificada** de todos os produtos
- **Deduplicação inteligente** evita redundância
- **Consulta centralizada** em todas as fontes
- **Escalabilidade** para adicionar novos sites

## Monitoramento

### 📊 **Métricas Disponíveis**
- Total de produtos por fonte (Cobasi, catálogos, web)
- Produtos enriquecidos vs básicos
- Taxa de duplicação detectada
- Performance de extração

### 🔍 **Logs Estruturados**
- Produtos novos vs atualizados
- Duplicatas encontradas e resolvidas
- Erros de extração e enriquecimento
- Tempo de processamento por fonte

## Próximos Passos

### 1. **Deploy e Teste**
- Fazer commit das mudanças
- Aguardar build do GitHub Actions
- Atualizar VPS com novas imagens
- Testar extração da Cobasi

### 2. **Validação**
- Verificar deduplicação funcionando
- Testar processamento de catálogos
- Confirmar enriquecimento web
- Monitorar performance

### 3. **Expansão**
- Adicionar outros sites (Petlove, Petz)
- Melhorar algoritmos de matching
- Implementar cache para consultas
- Otimizar performance de busca