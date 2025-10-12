# Guia de Deploy - Google Cloud Run

Este documento contém todas as instruções necessárias para fazer deploy da aplicação Agenda CAL no Google Cloud Run.

## Pré-requisitos

1. **Conta Google Cloud** com billing ativado
2. **gcloud CLI** instalado e configurado
   ```bash
   # Instalar gcloud CLI (se necessário)
   # https://cloud.google.com/sdk/docs/install
   
   # Login
   gcloud auth login
   
   # Configurar projeto
   gcloud config set project SEU_PROJECT_ID
   ```

3. **Docker** instalado localmente (para testes)

## Variáveis de Ambiente Necessárias

A aplicação requer **28 variáveis de ambiente**. Você precisará configurá-las no Cloud Run.

### Core Configuration (3)
- `CAL_SECRET` - Secret do webhook Cal.com
- `TZ` - Timezone (padrão: `America/Sao_Paulo`)
- `DATABASE_URL` - URL do PostgreSQL Cloud SQL (formato especial, ver abaixo)

### Notion Configuration (11)
- `NOTION_TOKEN` - Token de integração do Notion
- `NOTION_DB` - ID do database do Notion
- `NOTION_NAME_PROP` - Nome da coluna "Nome" (padrão: `Nome`)
- `NOTION_EMAIL_PROP` - Nome da coluna "Email" (padrão: `Email`)
- `NOTION_PHONE_PROP` - Nome da coluna "Telefone" (padrão: `Telefone`)
- `NOTION_STATUS_PROP` - Nome da coluna "Status" (padrão: `Status`)
- `NOTION_DATE_PROP` - Nome da coluna de data (padrão: `Data Agendada pelo Lead`)
- `NOTION_LINK_PROP` - Nome da coluna de link (padrão: `Link Flexge`)
- `NOTION_TEST_PROP` - Nome da coluna de teste (padrão: `Teste de Nivelamento`)
- `NOTION_IA_ATTENDANCE_PROP` - Nome da coluna IA (padrão: `Em atendimento pela IA`)
- `NOTION_STATUS_VALUE` - Valor do status de agendamento (padrão: `Agendado reunião`)

### Z-API Configuration - WhatsApp (4)
- `ZAPI_INSTANCE` - ID da instância Z-API
- `ZAPI_TOKEN` - Token da Z-API
- `ZAPI_CLIENT_TOKEN` - Client token da Z-API
- `ADMIN_PHONES` - Telefones dos admins separados por vírgula (ex: `5511999999999,5511888888888`)

### Flexge API Configuration (2)
- `FLEXGE_API_KEY` - API Key do Flexge
- `FLEXGE_BASE_URL` - URL base da API (padrão: `https://partner-api.flexge.com/external/placement-tests`)

### Zaia API Configuration (3)
- `ZAIA_API_KEY` - API Key da Zaia
- `ZAIA_AGENT_ID` - ID do agente Zaia
- `ZAIA_BASE_URL` - URL base da API (padrão: `https://api.zaia.app`)

### IDs Opcionais Notion (2)
- `NOTION_TEST_OPTION_ID_SIM` - ID da opção "Sim" no multi-select
- `NOTION_TEST_OPTION_ID_NAO` - ID da opção "Não" no multi-select

## Passo 1: Configurar Projeto e Habilitar APIs

```bash
# Definir variáveis
export PROJECT_ID="seu-project-id"
export REGION="us-central1"  # ou southamerica-east1 para São Paulo
export SERVICE_NAME="agenda-cal-service"

# Configurar projeto
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# Habilitar APIs necessárias
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Passo 2: Criar Cloud SQL Instance (PostgreSQL)

```bash
# Criar instância Cloud SQL PostgreSQL
gcloud sql instances create agenda-cal-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --backup \
  --backup-start-time=03:00 \
  --database-flags=max_connections=100

# Criar database
gcloud sql databases create scheduler_db \
  --instance=agenda-cal-db

# Criar usuário
gcloud sql users create appuser \
  --instance=agenda-cal-db \
  --password=ESCOLHA_UMA_SENHA_FORTE

# Anotar a connection string
gcloud sql instances describe agenda-cal-db --format="value(connectionName)"
# Resultado será algo como: PROJECT_ID:REGION:agenda-cal-db
```

### Formato do DATABASE_URL para Cloud SQL

```
postgresql://appuser:SUA_SENHA@/scheduler_db?host=/cloudsql/PROJECT_ID:REGION:agenda-cal-db
```

**Exemplo:**
```
postgresql://appuser:minhasenha123@/scheduler_db?host=/cloudsql/meu-projeto:us-central1:agenda-cal-db
```

## Passo 3: Build e Deploy Manual

### Opção A: Deploy Direto (Recomendado para primeira vez)

```bash
# Build e deploy em um comando
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --cpu=2 \
  --memory=1Gi \
  --timeout=300 \
  --concurrency=80 \
  --min-instances=1 \
  --max-instances=10 \
  --add-cloudsql-instances=$PROJECT_ID:$REGION:agenda-cal-db \
  --set-env-vars="TZ=America/Sao_Paulo" \
  --set-env-vars="CAL_SECRET=seu_cal_secret" \
  --set-env-vars="DATABASE_URL=postgresql://appuser:senha@/scheduler_db?host=/cloudsql/$PROJECT_ID:$REGION:agenda-cal-db"
```

**IMPORTANTE:** O comando acima configura apenas 3 variáveis de ambiente. Você precisará adicionar todas as outras 25 variáveis via Console ou usando múltiplos `--set-env-vars`.

### Opção B: Deploy com Cloud Build (Automatizado)

```bash
# Fazer build e deploy usando cloudbuild.yaml
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_REGION=$REGION,_TZ=America/Sao_Paulo
```

### Configurar Variáveis de Ambiente no Console

1. Acesse: https://console.cloud.google.com/run
2. Clique no serviço `agenda-cal-service`
3. Clique em "EDIT & DEPLOY NEW REVISION"
4. Na seção "Variables & Secrets", adicione todas as 28 variáveis
5. Clique em "DEPLOY"

## Passo 4: Configurar Variáveis via CLI (Alternativa)

Para configurar todas as variáveis de uma vez, crie um arquivo `env.yaml`:

```yaml
CAL_SECRET: "seu_cal_secret"
TZ: "America/Sao_Paulo"
DATABASE_URL: "postgresql://appuser:senha@/scheduler_db?host=/cloudsql/PROJECT_ID:REGION:agenda-cal-db"
NOTION_TOKEN: "seu_notion_token"
NOTION_DB: "seu_notion_db_id"
NOTION_NAME_PROP: "Nome"
NOTION_EMAIL_PROP: "Email"
NOTION_PHONE_PROP: "Telefone"
NOTION_STATUS_PROP: "Status"
NOTION_DATE_PROP: "Data Agendada pelo Lead"
NOTION_LINK_PROP: "Link Flexge"
NOTION_TEST_PROP: "Teste de Nivelamento"
NOTION_IA_ATTENDANCE_PROP: "Em atendimento pela IA"
NOTION_STATUS_VALUE: "Agendado reunião"
ZAPI_INSTANCE: "sua_instancia"
ZAPI_TOKEN: "seu_token"
ZAPI_CLIENT_TOKEN: "seu_client_token"
ADMIN_PHONES: "5511999999999,5511888888888"
FLEXGE_API_KEY: "sua_api_key"
FLEXGE_BASE_URL: "https://partner-api.flexge.com/external/placement-tests"
ZAIA_API_KEY: "sua_zaia_key"
ZAIA_AGENT_ID: "seu_agent_id"
ZAIA_BASE_URL: "https://api.zaia.app"
```

**IMPORTANTE:** NÃO comite este arquivo no Git! Adicione ao `.gitignore`.

Depois aplique:

```bash
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --update-env-vars-file=env.yaml
```

## Passo 5: Verificar Deploy

```bash
# Obter URL do serviço
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format="value(status.url)"

# Testar health check
curl https://SEU_SERVICE_URL/

# Ver logs
gcloud run services logs read $SERVICE_NAME \
  --region=$REGION \
  --limit=50
```

## Passo 6: Configurar Webhook do Cal.com

1. Acesse seu Cal.com
2. Vá em Settings → Webhooks
3. Adicione novo webhook:
   - URL: `https://SEU_SERVICE_URL/webhook/cal`
   - Events: `BOOKING_CREATED`, `BOOKING_RESCHEDULED`, `BOOKING_REQUESTED`
   - Secret: Use o mesmo valor de `CAL_SECRET`

## Testes da Aplicação

```bash
# Health check
curl https://SEU_SERVICE_URL/

# Testar configuração da Zaia
curl https://SEU_SERVICE_URL/test/zaia-config

# Testar verificação de placement tests
curl https://SEU_SERVICE_URL/test/placement-tests
```

## Conectar ao Cloud SQL Localmente (Para Debug)

```bash
# Instalar Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.2/cloud-sql-proxy.darwin.amd64
chmod +x cloud-sql-proxy

# Executar proxy
./cloud-sql-proxy $PROJECT_ID:$REGION:agenda-cal-db

# Em outro terminal, conectar com psql
psql "host=127.0.0.1 port=5432 sslmode=disable user=appuser dbname=scheduler_db"
```

## Monitoramento e Logs

### Ver logs em tempo real
```bash
gcloud run services logs tail $SERVICE_NAME --region=$REGION
```

### Ver métricas no Console
```bash
# Acessar métricas
open "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
```

### Alertas recomendados
- Request latency > 5s
- Error rate > 5%
- Instance count < 1 (min-instances não está funcionando)
- CPU utilization > 80%

## Atualizações e Rollback

### Fazer deploy de nova versão
```bash
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region=$REGION
```

### Listar revisões
```bash
gcloud run revisions list \
  --service=$SERVICE_NAME \
  --region=$REGION
```

### Rollback para revisão anterior
```bash
# Listar revisões
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION

# Fazer rollback
gcloud run services update-traffic $SERVICE_NAME \
  --region=$REGION \
  --to-revisions=REVISION_NAME=100
```

## Custos Estimados

Com a configuração recomendada:
- **Cloud Run**: ~$25-50/mês (1 instância mínima, 2 vCPU, 1Gi RAM)
- **Cloud SQL**: ~$10-20/mês (db-f1-micro com backup)
- **Cloud Build**: Primeiras 120 builds/dia são gratuitas
- **Container Registry**: ~$0.26/GB/mês de storage

**Total estimado: $35-70/mês**

Para reduzir custos:
- Remover `--min-instances=1` (mas o scheduler pode não funcionar consistentemente)
- Usar tier `db-g1-small` mais básico para Cloud SQL
- Reduzir CPU para 1 vCPU (mas pode afetar performance do scheduler)

## Troubleshooting

### Erro: "Cloud SQL connection failed"
- Verifique se a instância Cloud SQL está na mesma região
- Confirme que o `--add-cloudsql-instances` está correto
- Verifique o formato do DATABASE_URL

### Erro: "Port 8080 is not defined"
- Verifique se o Dockerfile expõe a porta correta
- Confirme que o código usa `PORT` do ambiente

### Scheduler não executa jobs
- Certifique-se que `--min-instances=1` está configurado
- Verifique logs para ver se o scheduler iniciou
- Confirme que DATABASE_URL está correto

### Timeout em requests
- Aumente `--timeout` (máximo 3600s)
- Verifique performance das APIs externas (Notion, Flexge, etc.)

## CI/CD com GitHub Actions (Opcional)

Crie `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud builds submit --config cloudbuild.yaml
```

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs: `gcloud run services logs read $SERVICE_NAME --region=$REGION`
2. Consulte a documentação do Cloud Run: https://cloud.google.com/run/docs
3. Verifique o status das APIs externas (Notion, Flexge, Zaia, Z-API)

## Referências

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)

