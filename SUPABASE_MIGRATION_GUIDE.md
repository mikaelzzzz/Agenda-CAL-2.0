# 🚀 Guia de Migração para Supabase

**Projeto:** agenda-cal-2-0  
**URL:** https://aczdfhxbnfyfdbnegafn.supabase.co  
**Data:** 2025-10-12

---

## ✅ Status

- [x] Conta Supabase criada
- [x] Projeto criado
- [x] Connection string obtida
- [ ] Migração de dados
- [ ] Cloud Run atualizado
- [ ] Testes realizados
- [ ] Render cancelado

---

## 📋 Informações do Projeto Supabase

**Project Reference:** `aczdfhxbnfyfdbnegafn`  
**Host:** `db.aczdfhxbnfyfdbnegafn.supabase.co`  
**Port:** `5432` (conexão direta) ou `6543` (pooler)  
**Database:** `postgres`  
**User:** `postgres`  

---

## 🔗 Connection Strings

### Connection Direta (Transaction Mode)
```
postgresql://postgres:[PASSWORD]@db.aczdfhxbnfyfdbnegafn.supabase.co:5432/postgres
```

**Usar para:**
- Migrações
- Scripts administrativos
- Operações que precisam de transações

### Connection Pooling (Session Mode)
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

**Usar para:**
- Aplicações serverless (Cloud Run)
- Alta concorrência
- **RECOMENDADO para produção**

---

## 🔄 Passo a Passo da Migração

### 1️⃣ Preparar Ambiente

```bash
# Navegar para o diretório do projeto
cd "/Users/mikaelzzzz/Downloads/Agenda CAL 2.0"

# Exportar URL do banco atual (Render)
export DATABASE_URL="postgresql://agenda_karol_2_0_user:UjBNLPcdEsmCT3S9TRI12v9tA06Mi4SM@dpg-d1r9q7vfte5s73cr66e0-a.oregon-postgres.render.com/agenda_karol_2_0"

# Verificar conexão com Render
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM apscheduler_jobs;"
```

### 2️⃣ Executar Migração Automática

```bash
# Substituir SENHA_SUPABASE pela sua senha real
./migrate_database.sh "postgresql://postgres:SENHA_SUPABASE@db.aczdfhxbnfyfdbnegafn.supabase.co:5432/postgres"
```

O script irá:
- ✅ Fazer backup do banco atual
- ✅ Testar conexão com Supabase
- ✅ Importar todos os dados
- ✅ Verificar integridade
- ✅ Mostrar próximos passos

### 3️⃣ Atualizar Cloud Run

**Importante:** Use a connection string com **pooler** para produção!

```bash
# Connection string com pooler (RECOMENDADO)
SUPABASE_URL="postgresql://postgres.aczdfhxbnfyfdbnegafn:SENHA_SUPABASE@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"

# Atualizar Cloud Run
gcloud run services update agenda-cal-2-0 \
  --region=southamerica-east1 \
  --update-env-vars="DATABASE_URL=$SUPABASE_URL"
```

### 4️⃣ Verificar Funcionamento

```bash
# Ver logs em tempo real
gcloud run services logs tail agenda-cal-2-0 --region=southamerica-east1

# Verificar se scheduler iniciou
curl https://agenda-cal-2-0-tw4udz5cza-rj.a.run.app/ | jq

# Verificar health
curl https://agenda-cal-2-0-tw4udz5cza-rj.a.run.app/test/zaia-config | jq
```

### 5️⃣ Monitorar (7 dias)

Durante 7 dias, monitore:
- ✅ Scheduler executando jobs corretamente
- ✅ Webhooks do Cal.com funcionando
- ✅ Integrações (Notion, Zaia, WhatsApp) ativas
- ✅ Sem erros nos logs

### 6️⃣ Cancelar Render

Após confirmar que tudo está funcionando:

1. Acesse: https://dashboard.render.com
2. Vá em "Databases"
3. Selecione `agenda_karol_2_0`
4. Settings → Delete Database
5. **Economia: $7/mês = $84/ano** 🎉

---

## 🔧 Troubleshooting

### Erro: "too many connections"

**Problema:** Muitas conexões abertas  
**Solução:** Use o pooler (porta 6543) no DATABASE_URL

```bash
# Mudar de:
postgresql://...@db.aczdfhxbnfyfdbnegafn.supabase.co:5432/postgres

# Para:
postgresql://postgres.aczdfhxbnfyfdbnegafn:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

### Erro: "connection timeout"

**Problema:** Timeout na conexão  
**Solução:** Verificar firewall ou usar pooler

```bash
# Testar conexão
psql "postgresql://..." -c "SELECT 1;"
```

### Scheduler não está executando

**Problema:** DATABASE_URL incorreto  
**Solução:** Verificar variável de ambiente

```bash
# Ver configuração atual
gcloud run services describe agenda-cal-2-0 \
  --region=southamerica-east1 \
  --format="value(spec.template.spec.containers[0].env)"
```

---

## 📊 Comparação: Antes vs Depois

| Feature | Render Starter | Supabase Free | Melhoria |
|---------|---------------|---------------|----------|
| **Custo/mês** | $7 | $0 | 💰 **-$7** |
| **Storage** | 10 GB | 500 MB | ⚠️ Menor |
| **Backup** | 7 dias | 7 dias | ✅ Igual |
| **RAM** | 256 MB | Compartilhada | ≈ Igual |
| **Uptime** | 100% | 100% | ✅ Igual |
| **Conexões** | 97 | Pool + 60 | ✅ Melhor |
| **Dashboard** | Básico | Rico | ✅ Melhor |
| **APIs** | Não | REST + GraphQL | 🎁 Bônus |
| **Auth** | Não | Incluído | 🎁 Bônus |
| **Storage** | Não | 1 GB | 🎁 Bônus |

**Conclusão:** Upgrade em features + Economia de $84/ano! 🎉

---

## 🎁 Features Extras do Supabase (Grátis!)

### 1. Dashboard Visual

Acesse: https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn

- 📊 **Table Editor:** Editar dados visualmente
- 📈 **Database Performance:** Monitorar queries
- 🔍 **SQL Editor:** Executar queries diretamente
- 📝 **Logs:** Ver logs em tempo real

### 2. REST API Automática

Todas as suas tabelas automaticamente têm uma API REST!

```bash
# Exemplo: Listar jobs do scheduler
curl https://aczdfhxbnfyfdbnegafn.supabase.co/rest/v1/apscheduler_jobs \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### 3. Real-time Subscriptions

Receba notificações quando dados mudam:

```javascript
// Em JavaScript
supabase
  .from('apscheduler_jobs')
  .on('INSERT', payload => {
    console.log('Novo job agendado:', payload)
  })
  .subscribe()
```

### 4. Authentication (Se precisar no futuro)

Sistema completo de autenticação:
- Email/Password
- OAuth (Google, GitHub, etc)
- Magic Links
- JWTs automáticos

### 5. Storage de Arquivos

1 GB grátis para armazenar arquivos:

```python
# Upload de arquivo
supabase.storage.from_('bucket').upload('file.pdf', file)
```

---

## 📱 Acessos Importantes

### Dashboard Principal
https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn

### Table Editor
https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn/editor

### SQL Editor
https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn/sql

### Database Settings
https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn/settings/database

### API Docs
https://supabase.com/dashboard/project/aczdfhxbnfyfdbnegafn/api

---

## 💾 Backup Manual (Opcional)

Para fazer backup manual a qualquer momento:

```bash
# Fazer backup
pg_dump "postgresql://postgres:[PASSWORD]@db.aczdfhxbnfyfdbnegafn.supabase.co:5432/postgres" > backup_$(date +%Y%m%d).sql

# Restaurar backup
psql "postgresql://..." < backup_20251012.sql
```

---

## 📞 Suporte

- **Documentação:** https://supabase.com/docs
- **Status:** https://status.supabase.com
- **Comunidade:** https://github.com/supabase/supabase/discussions
- **Discord:** https://discord.supabase.com

---

## ✅ Checklist Final

Após migração completa:

- [ ] Migração de dados concluída
- [ ] Cloud Run atualizado com novo DATABASE_URL
- [ ] Scheduler funcionando (verificar logs)
- [ ] Webhooks Cal.com testados
- [ ] Integrações Notion/Zaia/WhatsApp OK
- [ ] Monitoramento de 7 dias concluído
- [ ] Backup manual feito (segurança extra)
- [ ] Render cancelado
- [ ] **$84/ano economizados!** 🎉

---

**Próxima Revisão:** Após 7 dias de monitoramento
**Objetivo:** Confirmar estabilidade e cancelar Render

