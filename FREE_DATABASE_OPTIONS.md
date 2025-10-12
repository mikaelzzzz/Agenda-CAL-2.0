# 💰 Opções de Banco de Dados PostgreSQL GRATUITAS

**Objetivo:** Economizar os $6-7/mês que você paga atualmente no Render

## 🎯 Resumo Executivo

Sim! Existem **5 opções gratuitas excelentes** para substituir o Render Starter:

| Opção | Custo | Storage | Uptime | Backup | Região BR |
|-------|-------|---------|--------|--------|-----------|
| **Neon** | ✅ $0 | 512 MB | 100% | Não | ❌ |
| **Supabase** | ✅ $0 | 500 MB | 100% | Sim | ❌ |
| **Cloud SQL Free** | ✅ $0* | 30 GB | 100% | Sim | ❌ |
| **Render Free** | ✅ $0 | 1 GB | 90%** | Não | ❌ |
| **CockroachDB** | ✅ $0 | 5 GB | 100% | Sim | ❌ |

\* Limitado a regiões específicas dos EUA  
\** Database pode pausar após inatividade

---

## 🏆 OPÇÃO 1: Neon (RECOMENDADO) ⭐⭐⭐⭐⭐

**Site:** https://neon.tech

### ✅ Plano Free Forever

**Especificações:**
- **Storage:** 512 MB (suficiente para seu uso)
- **Compute:** 0.25 vCPU compartilhada
- **RAM:** Compartilhada (suficiente)
- **Projetos:** 10 projetos
- **Branches:** Ilimitados (git-like branches!)
- **Auto-pause:** Sim (após inatividade)
- **Uptime:** 100% (mas com auto-pause)
- **Conexões:** Pooling incluído (suporta muitas conexões)
- **Backup:** Ponto de restauração de 24h
- **Região:** US East (Virgínia), US West (Oregon), Europa

### ✨ Diferenciais
- ⚡ **Serverless** - Escala automaticamente
- 🌿 **Database Branching** - Git para bancos de dados!
- 🔌 **Connection Pooling** nativo (PgBouncer incluído)
- 📊 Monitoring incluído
- 🚀 Performance excelente

### ⚠️ Limitações
- Auto-pause após 5 minutos de inatividade (reconecta em ~1s)
- Storage limitado a 512 MB (mas suficiente para scheduler)

### 🎯 Adequação para Seu Uso
| Feature | Necessário | Disponível | Status |
|---------|-----------|------------|---------|
| Storage | < 500 MB | 512 MB | ✅ |
| Conexões | < 10 | Ilimitadas (pooling) | ✅ |
| Uptime | Alto | 100% | ✅ |
| Auto-pause OK? | Sim | Sim | ✅ |

**VEREDICTO:** 🟢 **PERFEITO PARA VOCÊ**

### Como Migrar

```bash
# 1. Criar conta no Neon
# Visite https://console.neon.tech/signup

# 2. Criar database
# Interface web ou CLI

# 3. Obter connection string
# Formato: postgresql://user:pass@ep-xxx.us-east-1.aws.neon.tech/dbname?sslmode=require

# 4. Atualizar Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --update-env-vars="DATABASE_URL=postgresql://user:pass@neon-host/dbname?sslmode=require"
```

---

## 🥈 OPÇÃO 2: Supabase ⭐⭐⭐⭐

**Site:** https://supabase.com

### ✅ Plano Free

**Especificações:**
- **Storage:** 500 MB
- **Database Size:** Ilimitado (contanto que < 500 MB)
- **RAM:** Compartilhada
- **Projetos:** 2 projetos ativos
- **Auto-pause:** Sim (após 7 dias de inatividade)
- **Uptime:** 100%
- **Conexões:** Pool de 60 conexões diretas + pooling
- **Backup:** Diário (7 dias de retenção)
- **Região:** US East, US West, Europa, Singapore

### ✨ Diferenciais
- 🔐 **Auth incluída** (pode substituir outras ferramentas)
- 🔄 **Real-time subscriptions** (WebSockets)
- 📦 **Storage de arquivos** incluído (1 GB)
- 🛠️ **Table Editor** visual
- 🔌 **REST API** automática para todas as tabelas
- 📊 Dashboard rico

### ⚠️ Limitações
- Pausa após 7 dias sem atividade (mas seu scheduler previne isso)
- Apenas 2 projetos ativos
- Suporte via comunidade apenas

### 🎯 Adequação para Seu Uso
| Feature | Necessário | Disponível | Status |
|---------|-----------|------------|---------|
| Storage | < 500 MB | 500 MB | ✅ |
| Conexões | < 10 | 60 diretas | ✅ |
| Backup | Desejável | 7 dias | ✅ |
| Uptime | Alto | 100% | ✅ |

**VEREDICTO:** 🟢 **EXCELENTE OPÇÃO**

### Como Migrar

```bash
# 1. Criar conta no Supabase
# Visite https://supabase.com/dashboard

# 2. Criar projeto
# Interface web (selecione região mais próxima)

# 3. Obter connection string
# Settings → Database → Connection string (Direct connection)

# 4. Atualizar Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --update-env-vars="DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
```

---

## 🥉 OPÇÃO 3: Google Cloud SQL Free Tier ⭐⭐⭐⭐

**Site:** https://cloud.google.com/sql

### ✅ Always Free Tier

**Especificações:**
- **Instância:** f1-micro (1 vCPU compartilhada, 0.6 GB RAM)
- **Storage:** 30 GB HDD (!)
- **Horas:** 750 horas/mês (suficiente para rodar 24/7)
- **Network Egress:** 1 GB/mês para América do Norte
- **Backup:** Automático (configurável)
- **Região:** Apenas regiões específicas dos EUA (NÃO Virginia)
  - us-central1 (Iowa)
  - us-west1 (Oregon)
  - us-east1 (Carolina do Sul)
- **Uptime:** 100%
- **SLA:** 99.95%

### ✨ Diferenciais
- 🔗 **Integração nativa** com Cloud Run
- 🔐 **Cloud SQL Proxy** para conexões seguras
- 💾 **30 GB de storage** (muito mais que outras opções)
- 📊 **Monitoring integrado** no Cloud Console
- ⚡ **Baixa latência** se usar mesma região do Cloud Run

### ⚠️ Limitações
- **Região limitada:** Apenas EUA (não pode usar São Paulo)
- **HDD apenas** (SSD custa extra)
- **Configuração complexa:** Requer Cloud SQL Proxy
- **Network egress** limitado (1 GB/mês)

### 🎯 Adequação para Seu Uso
| Feature | Necessário | Disponível | Status |
|---------|-----------|------------|---------|
| Storage | < 500 MB | 30 GB | ✅✅✅ |
| RAM | > 256 MB | 614 MB | ✅ |
| Uptime | Alto | 100% | ✅ |
| Região BR | Desejável | ❌ Não | ⚠️ |
| Integração | Importante | Nativa | ✅ |

**VEREDICTO:** 🟡 **BOA OPÇÃO, MAS SEM REGIÃO BR**

### Como Migrar

```bash
# 1. Habilitar Cloud SQL API
gcloud services enable sqladmin.googleapis.com

# 2. Criar instância free tier
gcloud sql instances create agenda-cal-db-free \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=HDD \
  --storage-size=10 \
  --no-storage-auto-increase \
  --backup \
  --backup-start-time=03:00

# 3. Criar database e usuário
gcloud sql databases create scheduler_db --instance=agenda-cal-db-free
gcloud sql users create appuser --instance=agenda-cal-db-free --password=SENHA_FORTE

# 4. Obter connection name
CONN_NAME=$(gcloud sql instances describe agenda-cal-db-free --format="value(connectionName)")

# 5. Atualizar Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --add-cloudsql-instances=$CONN_NAME \
  --update-env-vars="DATABASE_URL=postgresql://appuser:SENHA@/scheduler_db?host=/cloudsql/$CONN_NAME"
```

**⚠️ IMPORTANTE:** Você precisará migrar seu Cloud Run para `us-central1` OU aceitar latência extra entre São Paulo ↔ Iowa.

---

## 🎁 OPÇÃO 4: Render Free Tier ⭐⭐⭐

**Site:** https://render.com (você já usa!)

### ✅ Plano Free

**Especificações:**
- **Storage:** 1 GB
- **RAM:** 256 MB
- **Conexões:** 97
- **Auto-sleep:** Sim (após 15 minutos de inatividade)
- **Uptime:** ~90% (devido ao auto-sleep)
- **Backup:** ❌ Não incluído
- **Região:** Oregon (US West)

### ✨ Diferenciais
- 📦 **Mais storage** que outras opções gratuitas
- 🔧 **Você já conhece** a plataforma
- ⚡ **Migração zero** (já está lá!)

### ⚠️ Limitações
- ❌ **Sem backup** - CRÍTICO!
- 💤 **Auto-sleep** após 15 min - Pode impactar scheduler
- ⚠️ **Apenas 256 MB RAM** - Igual ao pago

### 🎯 Adequação para Seu Uso
| Feature | Necessário | Disponível | Status |
|---------|-----------|------------|---------|
| Storage | < 500 MB | 1 GB | ✅ |
| Backup | **Importante** | ❌ Não | 🔴 |
| Uptime | Alto | 90% (sleep) | ⚠️ |
| Auto-wake | Necessário | Sim | ✅ |

**VEREDICTO:** 🔴 **NÃO RECOMENDADO** (sem backup = risco de perda de dados)

### Como "Migrar" (Downgrade)

```bash
# No dashboard do Render:
# Settings → Downgrade to Free
# ⚠️ Você perderá os backups!
```

---

## 🚀 OPÇÃO 5: CockroachDB Serverless ⭐⭐⭐⭐

**Site:** https://cockroachlabs.com

### ✅ Plano Free

**Especificações:**
- **Storage:** 5 GB (!)
- **Request Units:** 50M RU/mês (equivale a ~250K queries)
- **RAM:** Serverless (escala automaticamente)
- **Uptime:** 100%
- **Backup:** Diário automático (30 dias de retenção)
- **Região:** Multi-região disponível
- **Compatibilidade:** PostgreSQL wire protocol

### ✨ Diferenciais
- 🌍 **Multi-região** - Alta disponibilidade global
- 💪 **5 GB de storage** - Mais que suficiente
- 🔄 **Backup de 30 dias** - Melhor que opções pagas
- ⚡ **Serverless** - Escala automática
- 🔐 **Enterprise-grade** - Usado por grandes empresas

### ⚠️ Limitações
- 📊 **Request Units limitados** - 50M/mês
- 🔌 **Não é PostgreSQL 100%** - Pequenas diferenças (mas compatível)
- 🧪 **Relativamente novo** no mercado serverless

### 🎯 Adequação para Seu Uso
| Feature | Necessário | Disponível | Status |
|---------|-----------|------------|---------|
| Storage | < 500 MB | 5 GB | ✅✅✅ |
| Backup | Desejável | 30 dias | ✅✅✅ |
| Uptime | Alto | 100% | ✅ |
| RU/mês | < 1M | 50M | ✅ |

**VEREDICTO:** 🟢 **EXCELENTE OPÇÃO** (mais storage + melhor backup)

### Como Migrar

```bash
# 1. Criar conta no CockroachDB
# Visite https://cockroachlabs.cloud/signup

# 2. Criar cluster serverless
# Interface web (selecione região)

# 3. Obter connection string
# Format: postgresql://user:pass@free-tier.gcp-us-central1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full

# 4. Atualizar Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --update-env-vars="DATABASE_URL=postgresql://user:pass@cockroach-host:26257/defaultdb?sslmode=verify-full"
```

---

## 📊 Comparação Completa

### Por Storage

```
CockroachDB: 5 GB     ████████████████████
Cloud SQL:   30 GB    ████████████████████████████████████████████████████████████
Render:      1 GB     ████
Supabase:    500 MB   ██
Neon:        512 MB   ██
```

### Por Backup

| Opção | Backup | Retenção | Custo |
|-------|--------|----------|-------|
| **CockroachDB** | ✅ Automático | 30 dias | $0 |
| **Supabase** | ✅ Automático | 7 dias | $0 |
| **Cloud SQL** | ✅ Configurável | Configurável | $0 |
| **Neon** | ⚠️ Ponto de restauração | 24h | $0 |
| **Render Free** | ❌ Não | - | $0 |

### Por Facilidade de Setup

| Opção | Dificuldade | Tempo | Documentação |
|-------|-------------|-------|--------------|
| **Neon** | ⭐ Fácil | 5 min | Excelente |
| **Supabase** | ⭐ Fácil | 5 min | Excelente |
| **Render** | ⭐ Fácil | 2 min | Boa |
| **CockroachDB** | ⭐⭐ Média | 10 min | Boa |
| **Cloud SQL** | ⭐⭐⭐ Difícil | 15 min | Complexa |

---

## 🎯 Recomendação Final

### 🏆 Para Você: **NEON** ou **SUPABASE**

**Escolha NEON se:**
- ✅ Quer o setup mais simples e rápido
- ✅ Gosta de tecnologia moderna (serverless)
- ✅ 512 MB é suficiente (é!)
- ✅ Database branching é interessante

**Escolha SUPABASE se:**
- ✅ Quer backup automático com 7 dias
- ✅ Pode aproveitar features extras (Auth, Storage, Real-time)
- ✅ Prefere dashboard mais rico
- ✅ Quer REST API automática

**Escolha COCKROACHDB se:**
- ✅ Quer o melhor backup (30 dias)
- ✅ Quer mais storage (5 GB)
- ✅ Valoriza multi-região

### ❌ Evite

- **Render Free:** Sem backup = risco de perda de dados
- **Cloud SQL Free:** Complexidade não vale a pena sem região BR

---

## 💸 Economia

### Atual
- **Render Starter:** $7/mês
- **Total/ano:** $84

### Com Opção Gratuita
- **Neon/Supabase/CockroachDB:** $0/mês
- **Total/ano:** $0
- **💰 ECONOMIA: $84/ano** 🎉

---

## 🚀 Plano de Migração Recomendado

### Fase 1: Testar em Paralelo (1 dia)

```bash
# 1. Criar conta no Neon ou Supabase
# 2. Criar database
# 3. Exportar dados atuais do Render
pg_dump $DATABASE_URL > backup.sql

# 4. Importar no novo banco
psql $NEW_DATABASE_URL < backup.sql

# 5. Testar localmente
export DATABASE_URL="novo_database_url"
python main.py
```

### Fase 2: Migrar Cloud Run (15 min)

```bash
# Atualizar DATABASE_URL no Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --update-env-vars="DATABASE_URL=NOVO_DATABASE_URL"

# Verificar logs
gcloud run services logs read agenda-cal-2-0 --region=southamerica-east1 --limit=50
```

### Fase 3: Monitorar (7 dias)

- Verificar scheduler está rodando
- Confirmar jobs executando corretamente
- Monitorar performance

### Fase 4: Cancelar Render (após confirmação)

```bash
# No dashboard do Render:
# Delete database instance
```

---

## ⚠️ Considerações Importantes

### Auto-Pause (Neon/Supabase)

**Problema:** Database pausa após inatividade  
**Solução:** Seu APScheduler roda a cada 3 horas, mantendo o banco ativo  
**Impacto:** Zero para seu caso

### Latência

**Render Oregon → Cloud Run SP:** ~180ms  
**Neon US-East → Cloud Run SP:** ~120ms  
**Supabase US-East → Cloud Run SP:** ~120ms  
**CockroachDB US-Central → Cloud Run SP:** ~140ms

**Impacto:** Desprezível para seu caso (scheduler não precisa de baixa latência)

### Migração de Dados

Seu banco é pequeno (< 100 MB provavelmente), então:
- ✅ Migração rápida (< 1 minuto)
- ✅ Downtime mínimo
- ✅ Rollback fácil se necessário

---

## 🎁 Bônus: Script de Migração Automática

Criarei um script para você migrar facilmente para Neon/Supabase!

```bash
#!/bin/bash
# migrate_database.sh

echo "🚀 Migrando banco de dados..."

# Variáveis
OLD_DB="$DATABASE_URL"  # Render atual
NEW_DB="$1"  # Novo database (passar como argumento)

# 1. Backup
echo "📦 Fazendo backup..."
pg_dump "$OLD_DB" > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Restaurar no novo banco
echo "📥 Importando dados..."
psql "$NEW_DB" < backup_*.sql

# 3. Verificar
echo "✅ Verificando..."
psql "$NEW_DB" -c "SELECT COUNT(*) FROM apscheduler_jobs;"

echo "🎉 Migração concluída!"
echo "👉 Próximo passo: Atualizar DATABASE_URL no Cloud Run"
```

---

## 📞 Suporte

- **Neon:** https://neon.tech/docs
- **Supabase:** https://supabase.com/docs
- **CockroachDB:** https://cockroachlabs.com/docs

---

**Resumo:** Migre para **NEON** ou **SUPABASE** e **economize $84/ano** mantendo mesma (ou melhor) qualidade! 🎉

