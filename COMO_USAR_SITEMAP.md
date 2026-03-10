# Como Usar a Importação via Sitemap

## Acesso Rápido

1. Acesse o frontend: `http://localhost:3000/dashboard/sitemap`
2. Ou via API diretamente

## Passo a Passo no Frontend

### 1. Configurar Sitemap
- Cole a URL do sitemap.xml (ex: `https://www.bbbpet.com.br/sitemap.xml`)
- Configure o filtro de URL (ex: `/produto/` para pegar apenas produtos)
- Defina o máximo de produtos (recomendado: 50 para teste)
- Escolha o ID do catálogo (padrão: 1)

### 2. Preview
- Clique em "Preview" para ver as URLs que serão processadas
- Verifique se o filtro está correto
- Veja quantas URLs foram encontradas

### 3. Testar Extração
- Clique em "Testar" em qualquer URL do preview
- Ou cole uma URL específica no campo "Testar Extração"
- Veja os dados extraídos: nome, marca, EAN, preço, descrição, imagens

### 4. Importar
- Se os testes estiverem OK, clique em "Importar Produtos"
- Aguarde o processamento (pode levar alguns minutos)
- Veja o resultado: quantos produtos foram importados

## Exemplo Prático

### Site: BBB Pet
```
URL Sitemap: https://www.bbbpet.com.br/sitemap.xml
Filtro: /produto/
Max Produtos: 50
```

### Site: Petlove
```
URL Sitemap: https://www.petlove.com.br/sitemap.xml
Filtro: /produto/
Max Produtos: 100
```

### Site: Petz
```
URL Sitemap: https://www.petz.com.br/sitemap.xml
Filtro: /p/
Max Produtos: 50
```

## Via API (cURL)

### Preview
```bash
curl -X POST "http://localhost:8000/api/sitemap/preview" \
  -H "Content-Type: application/json" \
  -d '{
    "sitemap_url": "https://www.bbbpet.com.br/sitemap.xml",
    "url_filter": "/produto/",
    "max_urls": 10
  }'
```

### Testar URL
```bash
curl -X POST "http://localhost:8000/api/sitemap/test-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.bbbpet.com.br/produto/areia-silica-cristal-tradicional-551"
  }'
```

### Importar
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

## Dicas

### Filtros de URL
- `/produto/` - URLs que contêm "/produto/"
- `/p/` - URLs que contêm "/p/"
- `.*-\d+$` - URLs que terminam com número
- `/categoria/(racao|areia)/` - Categorias específicas

### Performance
- Comece com 10-20 produtos para testar
- O sistema processa 10 URLs por vez
- Delay de 1 segundo entre lotes
- Para grandes volumes, aumente gradualmente

### Troubleshooting

**Nenhuma URL encontrada:**
- Verifique se o sitemap.xml está acessível
- Teste sem filtro primeiro
- Alguns sites têm múltiplos sitemaps

**Dados incompletos:**
- Cada site tem estrutura diferente
- O sistema tenta múltiplos seletores
- Produtos com apenas nome são salvos

**Timeout:**
- Reduza `max_products`
- Verifique conexão de internet
- Alguns sites são mais lentos

## Dados Extraídos

✅ Nome do produto (obrigatório)  
✅ Marca  
✅ EAN/código de barras  
✅ Preço  
✅ Descrição  
✅ Categoria  
✅ Imagens (até 5)  
✅ Especificações (peso, volume, dimensões)  

## Próximos Passos

Após importar:
1. Vá em "Produtos" para ver os importados
2. Execute deduplicação se necessário
3. Enriqueça com IA se desejar
4. Exporte para CSV/JSON

## Suporte

Se tiver problemas:
1. Teste uma URL específica primeiro
2. Verifique os logs do backend
3. Ajuste o filtro de URL
4. Reduza o número de produtos
