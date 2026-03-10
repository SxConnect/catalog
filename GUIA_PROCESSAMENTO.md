# Guia de Processamento de Catálogos

## O que acontece após fazer upload?

### 1. Upload (Instantâneo)
- ✅ Arquivo é enviado para o servidor
- ✅ Catálogo é registrado no banco de dados
- ✅ Status inicial: `uploaded`
- ⏱️ Tempo: 1-5 segundos (depende do tamanho do arquivo)

### 2. Processamento Assíncrono (Automático)
O sistema processa o PDF em background usando Celery Worker.

#### Etapas do Processamento:

**a) Extração de Páginas**
- 📄 Cada página do PDF é processada individualmente
- 🖼️ Imagens são extraídas e salvas
- 📝 Texto é extraído via OCR (Tesseract)
- ⏱️ Tempo: ~5-10 segundos por página

**b) Análise com IA**
- 🤖 OpenAI GPT analisa o texto extraído
- 🏷️ Identifica: nome, marca, EAN, categoria, descrição
- 📊 Gera score de confiança (0-1)
- ⏱️ Tempo: ~2-5 segundos por produto

**c) Deduplicação**
- 🔍 Verifica se produto já existe (por EAN ou nome+marca)
- ✏️ Se existe: atualiza informações
- ➕ Se não existe: cria novo produto
- ⏱️ Tempo: instantâneo

**d) Enriquecimento Web (Opcional)**
- 🌐 Busca dados adicionais na web
- 🖼️ Adiciona mais imagens
- 💰 Busca preços de referência
- 📦 Adiciona peso e dimensões
- ⏱️ Tempo: ~5-10 segundos por produto

### 3. Conclusão
- ✅ Status final: `completed`
- 📊 Produtos salvos no banco de dados
- 🎉 Pronto para consulta!

## Quanto tempo demora?

### Estimativa por Tamanho:

| Páginas | Produtos | Sem Enriquecimento | Com Enriquecimento |
|---------|----------|-------------------|-------------------|
| 10      | ~20      | 2-3 minutos       | 5-8 minutos       |
| 50      | ~100     | 10-15 minutos     | 25-40 minutos     |
| 100     | ~200     | 20-30 minutos     | 50-80 minutos     |
| 200     | ~400     | 40-60 minutos     | 100-160 minutos   |

### Fatores que Afetam o Tempo:

**Mais Rápido:**
- ✅ PDF com texto nativo (não escaneado)
- ✅ Imagens de boa qualidade
- ✅ Layout organizado
- ✅ Enriquecimento desabilitado

**Mais Lento:**
- ❌ PDF escaneado (precisa OCR)
- ❌ Imagens de baixa qualidade
- ❌ Layout complexo/desorganizado
- ❌ Enriquecimento habilitado
- ❌ Muitos produtos por página

## Como Acompanhar o Processamento?

### No Frontend (Recomendado)

1. **Acesse:** `http://localhost:3000/dashboard/upload`

2. **Após Upload:**
   - Barra de progresso aparece automaticamente
   - Atualização a cada 2 segundos
   - Mostra:
     - Página atual / Total de páginas
     - Porcentagem completa
     - Produtos encontrados
     - Tempo estimado restante

3. **Quando Completar:**
   - ✅ Mensagem de sucesso
   - 📊 Resumo: páginas, produtos, tempo
   - 🔗 Botão para ver produtos

### Via API

```bash
# Verificar status
curl http://localhost:8000/api/status/catalog/{catalog_id}/status

# Resposta:
{
  "catalog_id": 1,
  "filename": "catalogo.pdf",
  "status": "processing",
  "total_pages": 50,
  "processed_pages": 25,
  "progress_percentage": 50,
  "products_found": 48,
  "estimated_time_remaining_seconds": 300,
  "is_processing": true
}
```

### Logs do Backend

```bash
# Ver logs do worker
docker-compose logs -f worker

# Ver logs da API
docker-compose logs -f api
```

## O que fazer enquanto processa?

### ✅ Pode Fazer:
- Navegar em outras páginas do sistema
- Fazer upload de outro catálogo
- Consultar produtos já processados
- Configurar API keys
- Ajustar configurações

### ❌ Não Fazer:
- Fechar o navegador (processamento continua no servidor)
- Desligar o servidor
- Parar o worker (Celery)
- Deletar o arquivo PDF

## Troubleshooting

### Processamento Travado?

**Sintomas:**
- Progresso não avança por mais de 5 minutos
- Status fica em "processing" indefinidamente

**Soluções:**
```bash
# 1. Verificar se worker está rodando
docker-compose ps

# 2. Ver logs do worker
docker-compose logs worker

# 3. Reiniciar worker
docker-compose restart worker

# 4. Verificar Redis
docker-compose logs redis
```

### Processamento Falhou?

**Sintomas:**
- Status muda para "failed"
- Erro aparece nos logs

**Causas Comuns:**
1. PDF corrompido ou protegido
2. Falta de memória
3. Erro na API da OpenAI
4. Problema de conexão

**Soluções:**
1. Verificar logs: `docker-compose logs worker`
2. Tentar novamente com PDF menor
3. Verificar API key da OpenAI
4. Verificar conexão de internet

### Produtos Não Aparecem?

**Verificar:**
```bash
# 1. Status do catálogo
curl http://localhost:8000/api/status/catalog/1/status

# 2. Produtos do catálogo
curl http://localhost:8000/api/status/catalog/1/products

# 3. Todos os produtos
curl http://localhost:8000/api/products/search
```

## Otimização de Performance

### Para Processar Mais Rápido:

1. **Desabilitar Enriquecimento Web**
   - Reduz tempo em 50-70%
   - Pode enriquecer depois se necessário

2. **Usar PDFs com Texto Nativo**
   - Evita OCR (muito mais rápido)
   - Melhor qualidade de extração

3. **Aumentar Workers**
   ```yaml
   # docker-compose.yml
   worker:
     deploy:
       replicas: 3  # Múltiplos workers
   ```

4. **Aumentar Recursos**
   ```yaml
   worker:
     deploy:
       resources:
         limits:
           memory: 4G
           cpus: '2'
   ```

## Monitoramento

### Estatísticas Gerais
```bash
curl http://localhost:8000/api/status/stats

# Resposta:
{
  "total_catalogs": 10,
  "processing": 2,
  "completed": 7,
  "failed": 1,
  "total_products": 1543
}
```

### Catálogos Recentes
```bash
curl http://localhost:8000/api/status/recent?limit=10
```

## Próximos Passos

Após processamento completo:

1. **Ver Produtos**
   - `/dashboard/products` ou
   - `/api/products/search`

2. **Deduplicar**
   - `/api/deduplication/find-duplicates`
   - `/api/deduplication/merge/{id1}/{id2}`

3. **Exportar**
   - `/api/products/export/csv`
   - `/api/products/export/json`

4. **Enriquecer Manualmente**
   - Se desabilitou enriquecimento
   - Pode enriquecer produtos específicos depois

## Dicas Importantes

💡 **O processamento é assíncrono** - você não precisa ficar esperando na tela

💡 **Pode fechar o navegador** - o processamento continua no servidor

💡 **Use o preview** - teste com 10 páginas primeiro antes de processar tudo

💡 **Monitore os logs** - ajuda a identificar problemas rapidamente

💡 **Comece pequeno** - teste com catálogos menores primeiro

💡 **Enriquecimento é opcional** - pode fazer depois se necessário
