# Deploy Frontend - GHCR

## Status do Build

O workflow foi disparado com sucesso! 

### Acompanhar o Build

1. Acesse: https://github.com/SxConnect/catalog/actions
2. Procure pelo workflow "Build and Push Frontend Docker Image"
3. O build deve levar cerca de 5-10 minutos

### Após o Build Completar

Quando o workflow terminar com sucesso, a imagem estará disponível em:
```
ghcr.io/sxconnect/catalog-frontend:latest
```

### Deploy no Portainer

1. Acesse o Portainer
2. Vá em Stacks > catalog-stack
3. Clique em "Pull and redeploy"
4. Ou use o botão "Update the stack"

### Verificar a Imagem

Você pode verificar se a imagem foi publicada em:
https://github.com/orgs/SxConnect/packages?repo_name=catalog

### Variáveis de Ambiente Necessárias

Certifique-se de que estas variáveis estão configuradas no Portainer:

```env
# Frontend
NEXT_PUBLIC_API_URL=https://api.sxconnect.com.br
NEXTAUTH_URL=https://catalog.sxconnect.com.br
NEXTAUTH_SECRET=<sua-secret-gerada>
```

### Gerar NEXTAUTH_SECRET

Se ainda não gerou, use:
```bash
openssl rand -base64 32
```

### Troubleshooting

Se o build falhar:
1. Verifique os logs no GitHub Actions
2. Certifique-se de que o package-lock.json está correto
3. Verifique se todas as dependências estão instaladas

### Próximos Passos

1. ✅ Commit e push feitos
2. ⏳ Aguardar build no GitHub Actions (5-10 min)
3. ⏳ Fazer pull da nova imagem no Portainer
4. ⏳ Testar o frontend em produção
