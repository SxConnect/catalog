# Correções de CORS e API - Commit 40245ea

## Problemas Identificados

### 1. CORS Incompleto
- Faltava `expose_headers` e `max_age`
- Métodos não estavam explícitos
- Preflight requests não eram tratados corretamente

### 2. Endpoint `/api/admin/api-keys` (POST)
- Estava esperando parâmetros de query/form
- Frontend enviava JSON no body
- Causava erro 422 (Unprocessable Entity)

### 3. API URL no Frontend
- Configuração estava correta mas CORS bloqueava

## Correções Aplicadas

### 1. `catalog/app/main.py`
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://catalog.sxconnect.com.br",
        "https://catalog-api.sxconnect.com.br"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],  # NOVO
    max_age=3600,          # NOVO
)
```

### 2. `catalog/app/api/admin.py`
```python
from pydantic import BaseModel

class ApiKeyCreate(BaseModel):
    key: str
    provider: str = "groq"
    daily_limit: int = 14400

@router.post("/api-keys")
def create_api_key(
    data: ApiKeyCreate,  # MUDOU: agora aceita JSON
    db: Session = Depends(get_db)
):
    # Verificar se já existe
    existing = db.query(ApiKey).filter(ApiKey.key == data.key).first()
    # ... resto do código
```

## Próximos Passos

1. ✅ Commit e push realizados (commit `40245ea`)
2. ⏳ Aguardar build do GitHub Actions
3. ⏳ Fazer redeploy no Portainer:
   - Parar containers: `sixpet-catalog-api` e `sixpet-catalog-frontend`
   - Fazer pull das novas imagens
   - Iniciar containers novamente
4. ⏳ Testar endpoints:
   - `https://catalog-api.sxconnect.com.br/health`
   - `https://catalog-api.sxconnect.com.br/api/admin/settings`
   - `https://catalog-api.sxconnect.com.br/api/admin/api-keys`
5. ⏳ Verificar no frontend se CORS foi resolvido

## Comandos para Redeploy

```bash
# No Portainer, via Stack ou Containers:
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Verificação de Sucesso

- [ ] Frontend carrega sem erros de CORS no console
- [ ] Página de Upload funciona
- [ ] Página de API Keys funciona (adicionar/remover)
- [ ] Página de Settings funciona
- [ ] Página de Products funciona
- [ ] Exportação CSV funciona

## Erros Esperados (Resolvidos)

❌ ANTES:
```
Access to XMLHttpRequest at 'https://catalog-api.sxconnect.com.br/api/admin/settings' 
from origin 'https://catalog.sxconnect.com.br' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

✅ DEPOIS:
```
Status 200 OK
Access-Control-Allow-Origin: https://catalog.sxconnect.com.br
Access-Control-Allow-Credentials: true
```

❌ ANTES:
```
POST /api/admin/api-keys
Status: 422 Unprocessable Entity
```

✅ DEPOIS:
```
POST /api/admin/api-keys
Status: 200 OK
{ "id": 1, "key": "...", "provider": "groq", ... }
```
