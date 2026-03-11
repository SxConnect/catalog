# Normalização de Dados de Produtos

Este documento descreve o sistema de normalização de dados implementado no SixPet Catalog Engine.

## Visão Geral

O módulo `app.services.normalizer` fornece funções para normalizar e padronizar dados de produtos extraídos de catálogos PDF e páginas web, garantindo consistência e qualidade dos dados no banco.

## Funcionalidades

### 1. Normalização de Nomes de Produtos

**Função:** `normalize_product_name(name: str) -> str`

**Características:**
- Remove prefixos redundantes (produto:, item:, ração:, etc.)
- Aplica Title Case inteligente
- Preserva siglas conhecidas (EAN, SKU, DNA, DHA, etc.)
- Padroniza unidades de peso (15 Kg → 15kg)
- Remove caracteres especiais desnecessários

**Exemplos:**
```python
normalize_product_name("produto: Ração Golden 15 KG")
# Resultado: "Ração Golden 15kg"

normalize_product_name("item - Petisco com DNA especial")
# Resultado: "Petisco Com DNA Especial"
```

### 2. Normalização de Peso/Volume

**Função:** `normalize_weight(value: str) -> Tuple[Optional[float], Optional[str]]`

**Características:**
- Suporta múltiplos formatos (15 Kg, 15kg, 15 quilos)
- Converte vírgulas para pontos decimais
- Normaliza unidades (kg, g, ml, l, unidade)
- Retorna tupla (valor_numérico, unidade_normalizada)

**Exemplos:**
```python
normalize_weight("15 Kg")        # (15.0, "kg")
normalize_weight("500 ML")       # (500.0, "ml")
normalize_weight("1,5 litros")   # (1.5, "l")
normalize_weight("12 unidades")  # (12.0, "unidade")
```

### 3. Normalização de Marcas

**Função:** `normalize_brand(brand: str) -> str`

**Características:**
- Resolve aliases conhecidos (RC → Royal Canin)
- Aplica capitalização específica para marcas conhecidas
- Remove sufixos corporativos (Pet Nutrition, Ltda, etc.)
- Mantém capitalização correta (Hill's, não Hills)

**Exemplos:**
```python
normalize_brand("RC")                    # "Royal Canin"
normalize_brand("hill's pet nutrition")  # "Hill's"
normalize_brand("PURINA")               # "Nestlé Purina"
```

### 4. Validação de EAN

**Função:** `normalize_ean(ean: str) -> Optional[str]`

**Características:**
- Valida checksum EAN-13 e EAN-8
- Remove formatação (hífens, espaços)
- Retorna None se inválido
- Suporta códigos com formatação variada

**Exemplos:**
```python
normalize_ean("7891000100103")      # "7891000100103" (válido)
normalize_ean("789-1000-100103")    # "7891000100103" (limpa formatação)
normalize_ean("invalid")            # None (inválido)
```

## Integração no Sistema

### Pontos de Integração

1. **PDF Processor** (`app/tasks/pdf_processor.py`)
   - Normaliza dados antes de salvar produtos
   - Normaliza EAN antes de verificar duplicatas

2. **Sitemap Service** (`app/services/sitemap_service.py`)
   - Normaliza dados extraídos de páginas web
   - Garante consistência com dados de PDF

3. **Deduplication Service** (`app/services/deduplication_service.py`)
   - Normaliza EAN antes de buscar duplicatas
   - Melhora precisão da deduplicação

### Fluxo de Normalização

```
Dados Brutos (PDF/Web)
        ↓
Extração com IA/Scraping
        ↓
Normalização
        ↓
Verificação de Duplicatas
        ↓
Salvamento no Banco
```

## Configuração de Marcas

### Aliases de Marcas

O sistema mantém um mapa de aliases para marcas conhecidas:

```python
BRAND_ALIASES = {
    'RC': 'Royal Canin',
    'NC': 'Nestlé Purina',
    'PURINA': 'Nestlé Purina',
    'HILLS': "Hill's",
    # ... mais aliases
}
```

### Capitalização Específica

Marcas com capitalização específica são tratadas separadamente:

```python
BRAND_CAPITALIZATION = {
    'royal canin': 'Royal Canin',
    "hill's": "Hill's",
    'nestlé purina': 'Nestlé Purina',
    # ... mais marcas
}
```

## Testes

O módulo inclui testes abrangentes em `tests/test_normalizer.py`:

- **test_normalize_weight_variations()** - 30+ casos de teste para peso
- **test_normalize_ean_valid()** - Validação de EANs corretos
- **test_normalize_ean_invalid()** - Rejeição de EANs inválidos
- **test_normalize_brand_aliases()** - Resolução de aliases
- **test_normalize_product_name_*()** - Múltiplos cenários de nomes

### Executar Testes

```bash
# Executar todos os testes
python run_tests.py

# Executar apenas testes do normalizador
pytest tests/test_normalizer.py -v
```

## Extensibilidade

### Adicionar Nova Marca

1. Adicionar ao `BRAND_ALIASES` se for um alias
2. Adicionar ao `BRAND_CAPITALIZATION` se tiver capitalização específica
3. Adicionar teste correspondente

### Adicionar Nova Unidade

1. Adicionar padrão regex em `normalize_weight()`
2. Adicionar normalização da unidade
3. Adicionar casos de teste

### Adicionar Nova Sigla

1. Adicionar à lista `PRESERVE_ACRONYMS`
2. Adicionar teste de preservação

## Performance

- **Normalização de nome:** ~0.1ms por produto
- **Validação de EAN:** ~0.05ms por código
- **Normalização de peso:** ~0.02ms por valor
- **Normalização de marca:** ~0.01ms por marca

O impacto na performance é mínimo e os benefícios de qualidade de dados compensam amplamente o overhead.