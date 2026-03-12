# Opções de Instalação do MinIO

O instalador agora oferece duas opções de configuração do MinIO para atender diferentes necessidades.

## 🔧 MinIO Completo (Recomendado)

### Características:
- **API S3 completa** para storage de objetos
- **Console Web avançado** para gerenciamento
- **Criação automática de buckets** essenciais
- **Configuração otimizada** para produção

### Buckets criados automaticamente:
- `sixpet-catalog` - Para o sistema de catálogo
- `evolution` - Para Evolution API
- `papi` - Para PAPI (Pastorini API)
- `afiliados` - Para sistema de afiliados
- `flixly` - Para plataforma Flixly

### Vantagens:
- ✅ **Setup automático** - Buckets prontos para uso
- ✅ **Configuração otimizada** - Labels Traefik aprimorados
- ✅ **Pronto para produção** - Sem configuração manual
- ✅ **Política pública** - Bucket sixpet-catalog acessível publicamente

### Quando usar:
- Instalação nova completa
- Ambiente de produção
- Quando você quer tudo funcionando automaticamente
- Para projetos que usam múltiplos buckets

## 📦 MinIO Simples

### Características:
- **API S3 básica** para storage
- **Console Web básico** para acesso
- **Configuração manual** de buckets
- **Setup mínimo** sem automação

### Vantagens:
- ✅ **Configuração leve** - Menos recursos utilizados
- ✅ **Controle total** - Você cria apenas os buckets necessários
- ✅ **Compatível** - Mesma configuração que estava rodando
- ✅ **Flexível** - Adapta-se às suas necessidades específicas

### Quando usar:
- Restauração da configuração anterior
- Ambiente de desenvolvimento/teste
- Quando você quer controle total sobre buckets
- Para projetos com necessidades específicas

## 🔄 Diferenças Técnicas

### Labels Traefik:
**Completo:**
```yaml
- traefik.http.routers.minio_s3.rule=Host(`s3.domain.com`)
- traefik.http.routers.minio_s3.service=minio_s3
- traefik.http.services.minio_s3.loadbalancer.passHostHeader=true
```

**Simples:**
```yaml
- traefik.http.routers.minio_public.rule=Host(`s3.domain.com`)
- traefik.http.routers.minio_public.service=minio_public
```

### Serviços adicionais:
**Completo:** Inclui container `minio-setup` para criação automática de buckets
**Simples:** Apenas o container principal do MinIO

## 📋 Recomendações

### Use MinIO Completo se:
- É uma instalação nova
- Quer tudo funcionando automaticamente
- Vai usar múltiplos serviços (Catalog, Evolution, PAPI, etc.)
- Prefere configuração otimizada

### Use MinIO Simples se:
- Está restaurando a configuração anterior
- Quer controle total sobre buckets
- Tem necessidades específicas de configuração
- Prefere setup manual

## 🚀 Migração entre versões

### De Simples para Completo:
1. Pare a stack MinIO atual
2. Recrie usando a opção "Completo"
3. Os dados existentes serão preservados
4. Novos buckets serão criados automaticamente

### De Completo para Simples:
1. Pare a stack MinIO atual
2. Recrie usando a opção "Simples"
3. Os buckets existentes serão mantidos
4. Remova buckets desnecessários manualmente se desejar

## 💡 Dicas

- **Backup sempre** antes de alterar configurações
- **Teste em ambiente de desenvolvimento** antes da produção
- **Monitore logs** após mudanças de configuração
- **Documente** quais buckets são necessários para seu projeto