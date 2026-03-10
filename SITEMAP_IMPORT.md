# Importação de Produtos via Sitemap

Sistema para extrair dados de produtos diretamente de sitemaps XML de sites de e-commerce.

## Como Funciona

1. O sistema lê o sitemap.xml do site
2. Extrai todas as URLs de produtos
3. Faz scraping de cada página para extrair:
   - Nome do produto
   - Marca
   - EAN/código de barras
   - Preço
   - Descrição
   - Categoria
   - Imagens
   - Especificações (peso, volume, dimensões)

## Endpoints Disponíveis

### 1. Preview do Sitemap
Visualiza as URLs que serão processadas antes de importar.

```bash
POST /api/sitemap/preview
```

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/sitemap/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 10
  }'
```

**Resposta:**
```json
{
  "total_urls": 10,
  "sample_urls": [
    {
      "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551",
      "lastmod": "2025-11-25",
      "priority": "1.0",
      "changefreq": "weekly"
    }
  ],
  "filter_applied": "/produto/"
}
```

### 2. Testar Scraping de URL
Testa a extração de dados de uma URL específica.

```bash
POST /api/sitemap/test-scrape
```

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/sitemap/test-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"
  }'
```

**Resposta:**
```json
{
  "status": "success",
  "product_data": {
    "source_url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-551",
    "name": "Areia Sílica Cristal Tradicional",
    "brand": "BBB Pet",
    "ean": "7898123456789",
    "price": 45.90,
    "description": "Areia higiênica de sílica para gatos...",
    "category": "Higiene > Areia para Gatos",
    "images": [
      "https://www.bbbpet.com.br/images/produto1.jpg",
      "https://www.bbbpet.com.br/images/produto2.jpg"
    ],
    "specifications": {
      "weight": "3.6 kg"
    }
  }
}
```

### 3. Importar Produtos do Sitemap
Importa todos os produtos do sitemap para o catálogo.

```bash
POST /api/sitemap/import
```

**Exemplo:**
```bash
curl -X POST "http://localhost:8000/api/sitemap/import" \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "catalog_id": 1,
    "url_filter": "/produto/",
    "max_products": 100,
    "auto_save": true
  }'
```

**Parâmetros:**
- `sitemap_url`: URL do sitemap.xml
- `catalog_id`: ID do catálogo onde salvar os produtos
- `url_filter`: (Opcional) Regex para filtrar URLs (ex: "/produto/")
- `max_products`: (Opcional) Limite máximo de produtos a processar
- `auto_save`: Se true, salva automaticamente no banco de dados

**Resposta:**
```json
{
  "status": "success",
  "message": "Successfully imported 95 products from sitemap",
  "total_urls": 100,
  "products_extracted": 95,
  "products_saved": 95,
  "errors": [
    "Error saving product X: duplicate EAN"
  ]
}
```

## Exemplo Completo de Uso

### Passo 1: Preview do Sitemap
```bash
curl -X POST "http://localhost:8000/api/sitemap/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 5
  }'
```

### Passo 2: Testar uma URL
```bash
curl -X POST "http://localhost:8000/api/sitemap/test-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"
  }'
```

### Passo 3: Importar Produtos
```bash
curl -X POST "http://localhost:8000/api/sitemap/import" \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "catalog_id": 1,
    "url_filter": "/produto/",
    "max_products": 50,
    "auto_save": true
  }'
```

## Filtros de URL

Use regex para filtrar apenas URLs de produtos:

- `/produto/` - URLs que contêm "/produto/"
- `/produto/.*-\d+$` - URLs que terminam com número (ID do produto)
- `/(ração|areia|brinquedo)/` - URLs de categorias específicas

## Comportamento de Duplicatas

O sistema verifica duplicatas por:
1. EAN (se disponível)
2. Nome + Marca

Se encontrar duplicata:
- Atualiza descrição, categoria, preço e imagens
- Mantém o produto original

Se não encontrar:
- Cria novo produto no catálogo

## Performance

- Processa em lotes de 10 URLs por vez
- Delay de 1 segundo entre lotes
- Timeout de 30 segundos por requisição
- Recomendado: usar `max_products` para testes iniciais

## Dados Extraídos

O sistema tenta extrair automaticamente:

✅ Nome do produto  
✅ Marca  
✅ EAN/GTIN  
✅ Preço  
✅ Descrição  
✅ Categoria  
✅ Imagens (até 5)  
✅ Peso/Volume/Dimensões  

## Troubleshooting

### Nenhum produto extraído
- Verifique se o `url_filter` está correto
- Teste uma URL específica com `/test-scrape`
- Alguns sites podem bloquear scraping

### Dados incompletos
- Cada site tem estrutura HTML diferente
- O sistema usa múltiplos seletores para tentar extrair dados
- Produtos com dados mínimos (apenas nome) são salvos

### Timeout
- Reduza `max_products`
- Alguns sites são mais lentos
- Verifique conexão de internet

## Próximos Passos

Após importar:
1. Revise os produtos em `/api/products/search`
2. Execute deduplicação se necessário
3. Enriqueça com IA se desejar
4. Exporte para CSV/JSON
