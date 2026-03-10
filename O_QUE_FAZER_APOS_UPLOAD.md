# O que fazer após fazer upload do catálogo?

## ❌ ANTES (v1.0.6)
- Upload do PDF
- ❓ Esperar sem saber o que está acontecendo
- ❓ Não sabe quanto tempo vai demorar
- ❓ Não sabe quantos produtos foram encontrados
- ✅ Eventualmente os produtos aparecem

## ✅ AGORA (v1.0.7)

### 1. Após fazer upload, você vê IMEDIATAMENTE:

```
┌─────────────────────────────────────────────────┐
│ 🔄 Processando: catalogo_pet.pdf                │
│                                                  │
│ Página 25 de 50                                 │
│ ████████████████░░░░░░░░░░░░░░░░░░░░ 50%       │
│                                                  │
│ 48 produtos encontrados                         │
│ Tempo estimado: 5m 30s                          │
│                                                  │
│ Aguarde o processamento terminar...             │
└─────────────────────────────────────────────────┘
```

### 2. A tela atualiza AUTOMATICAMENTE a cada 2 segundos

Você vê em tempo real:
- ✅ Qual página está sendo processada
- ✅ Porcentagem completa
- ✅ Quantos produtos já foram encontrados
- ✅ Quanto tempo falta (estimativa)

### 3. Você PODE:

#### ✅ Fechar o navegador
O processamento continua no servidor! Você pode:
- Ir tomar um café ☕
- Fazer outras coisas
- Voltar depois para ver o resultado

#### ✅ Navegar em outras páginas
- Ver produtos já processados
- Configurar API keys
- Fazer outro upload
- Usar importação via sitemap

#### ✅ Acompanhar de outro dispositivo
- Abra em outro computador
- Abra no celular
- O progresso é o mesmo em todos

### 4. Quando COMPLETAR:

```
┌─────────────────────────────────────────────────┐
│ ✅ Processamento Concluído!                     │
│                                                  │
│ catalogo_pet.pdf                                │
│                                                  │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│ │   50    │  │   95    │  │  100%   │         │
│ │ Páginas │  │Produtos │  │Completo │         │
│ └─────────┘  └─────────┘  └─────────┘         │
│                                                  │
│ [Processar Novo Catálogo]                       │
└─────────────────────────────────────────────────┘
```

## ⏱️ Quanto tempo demora?

### Estimativas:

| Páginas | Produtos | Sem Enriquecimento | Com Enriquecimento |
|---------|----------|-------------------|-------------------|
| 10      | ~20      | 2-3 min           | 5-8 min           |
| 50      | ~100     | 10-15 min         | 25-40 min         |
| 100     | ~200     | 20-30 min         | 50-80 min         |
| 200     | ~400     | 40-60 min         | 100-160 min       |

### Fatores que afetam:

**Mais Rápido:**
- ✅ PDF com texto nativo (não escaneado)
- ✅ Imagens de boa qualidade
- ✅ Layout organizado
- ✅ Enriquecimento desabilitado

**Mais Lento:**
- ❌ PDF escaneado (precisa OCR)
- ❌ Imagens ruins
- ❌ Layout bagunçado
- ❌ Enriquecimento habilitado

## 🔍 Como acompanhar?

### Opção 1: Frontend (Recomendado)
Acesse: `https://catalog.sxconnect.com.br/dashboard/upload`

Você verá:
- Barra de progresso
- Páginas processadas
- Produtos encontrados
- Tempo estimado
- Histórico de uploads

### Opção 2: API
```bash
# Verificar status
curl https://catalog-api.sxconnect.com.br/api/status/catalog/1/status

# Resposta:
{
  "catalog_id": 1,
  "filename": "catalogo.pdf",
  "status": "processing",
  "total_pages": 50,
  "processed_pages": 25,
  "progress_percentage": 50,
  "products_found": 48,
  "estimated_time_remaining_seconds": 330,
  "is_processing": true
}
```

### Opção 3: Logs do Servidor
```bash
# Ver logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f worker

# Você verá:
# [INFO] Processing page 25/50
# [INFO] AI extracted product: Ração Premium - Marca X
# [INFO] Created new product: Ração Premium
```

## 📊 O que acontece durante o processamento?

### Etapa 1: Extração (5-10s por página)
```
📄 Página 1
  ├─ 🖼️ Extraindo imagens
  ├─ 📝 Extraindo texto (OCR)
  └─ ✅ Página processada
```

### Etapa 2: Análise com IA (2-5s por produto)
```
🤖 Analisando texto
  ├─ 🏷️ Nome: Ração Premium Cães Adultos
  ├─ 🏢 Marca: Marca X
  ├─ 📦 EAN: 7891234567890
  ├─ 📂 Categoria: Alimentação
  └─ ✅ Produto estruturado
```

### Etapa 3: Deduplicação (instantâneo)
```
🔍 Verificando duplicatas
  ├─ ❌ EAN não encontrado
  ├─ ❌ Nome+Marca não encontrado
  └─ ✅ Criar novo produto
```

### Etapa 4: Enriquecimento (5-10s - opcional)
```
🌐 Buscando dados na web
  ├─ 🖼️ Encontrou 3 imagens
  ├─ 💰 Preço médio: R$ 89,90
  ├─ 📦 Peso: 15kg
  └─ ✅ Produto enriquecido
```

## 🎯 Após Conclusão

### 1. Ver Produtos
```bash
# Via Frontend
https://catalog.sxconnect.com.br/dashboard/products

# Via API
curl https://catalog-api.sxconnect.com.br/api/products/search
```

### 2. Verificar Duplicatas
```bash
# Via API
curl https://catalog-api.sxconnect.com.br/api/deduplication/find-duplicates
```

### 3. Exportar
```bash
# CSV
curl https://catalog-api.sxconnect.com.br/api/products/export/csv > produtos.csv

# JSON
curl https://catalog-api.sxconnect.com.br/api/products/export/json > produtos.json
```

### 4. Enriquecer Manualmente (se desabilitou)
```bash
# Buscar dados de um produto específico
curl -X POST https://catalog-api.sxconnect.com.br/api/products/enrich/123
```

## 🆘 E se travar?

### Sintomas:
- Progresso não avança por mais de 5 minutos
- Status fica em "processing" indefinidamente

### Soluções:

#### 1. Verificar Worker
```bash
docker-compose -f docker-compose.prod.yml logs worker
```

#### 2. Verificar Redis
```bash
docker-compose -f docker-compose.prod.yml logs redis
```

#### 3. Restart Worker
```bash
docker-compose -f docker-compose.prod.yml restart worker
```

#### 4. Ver Status via API
```bash
curl https://catalog-api.sxconnect.com.br/api/status/catalog/1/status
```

## 💡 Dicas

### Para Processar Mais Rápido:
1. **Desabilite enriquecimento** (reduz 50-70% do tempo)
2. **Use PDFs com texto nativo** (evita OCR)
3. **Teste com 10 páginas primeiro**
4. **Processe em horários de baixo uso**

### Para Melhor Qualidade:
1. **Habilite enriquecimento** (mais dados da web)
2. **Use PDFs de alta qualidade**
3. **Revise produtos após processamento**
4. **Execute deduplicação**

## 📱 Notificações (Futuro)

Em breve você poderá:
- ✉️ Receber email quando completar
- 📱 Notificação no Slack
- 🔔 Webhook customizado
- 📊 Relatório automático

## 🎓 Resumo

**Antes:** Esperar sem saber nada  
**Agora:** Acompanhar tudo em tempo real

**Você pode:**
- ✅ Ver progresso ao vivo
- ✅ Fechar navegador (continua processando)
- ✅ Fazer outras coisas
- ✅ Voltar depois
- ✅ Acompanhar de qualquer lugar

**Tempo:** Depende do tamanho (veja tabela acima)

**Resultado:** Produtos salvos e prontos para uso!

---

**Dúvidas?** Veja `GUIA_PROCESSAMENTO.md` para mais detalhes.
