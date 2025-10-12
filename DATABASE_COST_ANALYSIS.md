# Análise de Custos: Render PostgreSQL vs Google Cloud SQL

**Data da Análise:** 2025-10-12  
**Banco Atual:** Render PostgreSQL  
**Custo Atual:** $6/mês

## 📊 Configuração Atual no Render

Com base no DATABASE_URL identificado:
- **Host:** `dpg-d1r9q7vfte5s73cr66e0-a.oregon-postgres.render.com`
- **Database:** `agenda_karol_2_0`
- **Região:** Oregon (US West)

### Planos Disponíveis no Render (2025)

| Plano | Preço/Mês | RAM | Storage | Conexões | Backup |
|-------|-----------|-----|---------|----------|--------|
| **Free** | $0 | 256 MB | 1 GB | 97 | Não |
| **Starter** | **$7** | 256 MB | 10 GB | 97 | Sim (7 dias) |
| **Standard** | $25 | 2 GB | 100 GB | 497 | Sim (7 dias) |
| **Pro** | $90 | 8 GB | 512 GB | 997 | Sim (14 dias) |

**Seu plano atual:** Provavelmente **Starter** ($7/mês, ou $6 com desconto promocional)

### Especificações do Plano Starter
- **RAM:** 256 MB
- **Storage:** 10 GB SSD
- **Conexões Máximas:** 97
- **Backup Automático:** 7 dias de retenção
- **Alta Disponibilidade:** Não
- **PostgreSQL:** Versão 15 ou 16

## 💰 Opções no Google Cloud SQL

### Opção 1: db-f1-micro (Mais Próximo ao Render Starter)

**Especificações:**
- **CPU:** 1 vCPU compartilhada
- **RAM:** 614 MB (0.6 GB)
- **Storage:** 10 GB SSD (configurável)
- **Região:** us-central1 (Iowa) ou southamerica-east1 (São Paulo)

**Custos Mensais:**
| Componente | Custo |
|------------|-------|
| Instância (db-f1-micro) | ~$7.67/mês |
| Storage (10 GB SSD) | $1.70/mês |
| Backup (10 GB) | $0.80/mês |
| **TOTAL** | **~$10.17/mês** |

**⚠️ Diferença:** +$4.17/mês (+70% mais caro)

### Opção 2: db-g1-small (Melhor Performance)

**Especificações:**
- **CPU:** 1 vCPU compartilhada
- **RAM:** 1.7 GB
- **Storage:** 10 GB SSD

**Custos Mensais:**
| Componente | Custo |
|------------|-------|
| Instância (db-g1-small) | ~$26.30/mês |
| Storage (10 GB SSD) | $1.70/mês |
| Backup (10 GB) | $0.80/mês |
| **TOTAL** | **~$28.80/mês** |

**⚠️ Diferença:** +$22.80/mês (+380% mais caro)

### Opção 3: Instância Dedicada (db-custom-1-3840)

**Especificações:**
- **CPU:** 1 vCPU dedicada
- **RAM:** 3.75 GB
- **Storage:** 10 GB SSD

**Custos Mensais:**
| Componente | Custo |
|------------|-------|
| CPU (1 vCPU) | ~$29.74/mês |
| RAM (3.75 GB) | ~$18.90/mês |
| Storage (10 GB SSD) | $1.70/mês |
| Backup (10 GB) | $0.80/mês |
| **TOTAL** | **~$51.14/mês** |

**⚠️ Diferença:** +$45.14/mês (+752% mais caro)

## 🔍 Análise Detalhada dos Custos

### Custos Adicionais no Google Cloud SQL

1. **Transferência de Dados (Egress)**
   - Dentro da mesma região: Grátis
   - Para Cloud Run (mesma região): Grátis
   - Para internet: $0.12/GB (primeiros 1TB/mês)

2. **Operações de I/O**
   - Incluídas no preço da instância (sem custo adicional)

3. **Backup Automático**
   - Primeiros 10 GB: Gratuitos
   - Adicional: $0.08/GB/mês

4. **Alta Disponibilidade (HA)**
   - Se habilitado: +100% do custo da instância

### Tabela Comparativa Resumida

| Feature | Render Starter | Cloud SQL f1-micro | Cloud SQL g1-small |
|---------|---------------|--------------------|--------------------|
| **Preço/Mês** | **$6-7** | **$10.17** | **$28.80** |
| RAM | 256 MB | 614 MB | 1.7 GB |
| Storage | 10 GB | 10 GB | 10 GB |
| Conexões | 97 | Ilimitadas* | Ilimitadas* |
| Backup | 7 dias | Configurável | Configurável |
| Região BR | ❌ Não | ✅ Sim (SP) | ✅ Sim (SP) |
| HA | ❌ Não | ✅ Opcional | ✅ Opcional |
| Escalabilidade | Manual | Automática | Automática |
| SLA | 99.9% | 99.95% | 99.95% |

\* Limitado por RAM e CPU disponível

## 📈 Estimativa de Uso Atual

Com base na sua aplicação:
- **Scheduler:** APScheduler com jobs a cada 3 horas
- **Webhooks:** Cal.com (volume baixo/médio)
- **Storage Necessário:** < 1 GB (apenas jobs do scheduler)
- **Conexões Simultâneas:** < 10 típicas

**Conclusão:** Seu uso é **LEVE**, adequado para planos básicos.

## 💡 Recomendações

### ❌ NÃO Recomendo Migrar para Cloud SQL

**Motivos:**
1. **Custo 70% maior** ($10.17 vs $6-7/mês) para o plano mais barato
2. **Mesmo desempenho** (256MB vs 614MB não fará diferença significativa)
3. **Setup mais complexo** (requer Cloud SQL Proxy para conexão segura)
4. **Sem benefício real** para seu caso de uso (baixo volume)

### ✅ Recomendo Continuar no Render

**Motivos:**
1. **Custo-benefício superior** para aplicações pequenas
2. **Simplicidade** na configuração e manutenção
3. **Backup automático** incluído
4. **Já está funcionando** perfeitamente

## 🎯 Quando Migrar para Cloud SQL?

Considere migrar apenas se:

1. **Volume crescer significativamente**
   - Mais de 100 conexões simultâneas
   - Mais de 50 GB de dados
   - Milhares de webhooks/hora

2. **Necessitar de recursos avançados**
   - Alta disponibilidade (99.99% SLA)
   - Réplicas de leitura
   - Point-in-time recovery
   - Insights avançados de performance

3. **Quiser consolidar tudo no Google Cloud**
   - Simplificação de billing
   - Mesma região que Cloud Run (latência mínima)
   - Integração nativa com Cloud Run

## 💸 Alternativas para Economizar

### No Render (Atual)
1. ✅ **Manter plano Starter** - Melhor custo-benefício
2. ⚠️ Downgrade para Free ($0) - Mas perde backup e tem apenas 1GB

### No Google Cloud
1. **Usar AlloyDB Omni** (quando disponível)
   - Preços competitivos
   - Performance superior

2. **Considerar Cloud Run + Cloud Firestore**
   - Para jobs do scheduler apenas
   - Datastore: $0.06 por 100K reads
   - Poderia eliminar necessidade de PostgreSQL

3. **Instância preemptiva** (não recomendado para produção)
   - 60-80% de desconto
   - Mas pode ser desligada a qualquer momento

## 📊 Cálculo de Breakeven

Para que o Cloud SQL valha a pena em termos de custo, você precisaria:

1. **Usar recursos que o Render não oferece**
   - HA com failover automático
   - Point-in-time recovery
   - Réplicas de leitura

2. **Ou ter economia em outros lugares**
   - Eliminar outro serviço
   - Créditos do Google Cloud ($300 para novos clientes)

## 🎁 Créditos do Google Cloud

Se você for **novo cliente** no Google Cloud:
- **$300 em créditos** válidos por 90 dias
- Cobriria ~30 meses de db-f1-micro
- Cobriria ~10 meses de db-g1-small

**Neste caso:** Vale a pena migrar temporariamente para testar!

## 📝 Conclusão Final

### Situação Atual
- **Render PostgreSQL Starter:** $6-7/mês
- **Uso:** Leve (scheduler + webhooks ocasionais)
- **Performance:** Adequada

### Recomendação

#### 🏆 OPÇÃO 1: Manter Render (RECOMENDADO)
**Custo:** $6-7/mês  
**Prós:** Mais barato, simples, já funciona  
**Contras:** Sem região no Brasil, SLA 99.9%

#### 🥈 OPÇÃO 2: Testar Cloud SQL com Créditos
**Custo:** $0 (com créditos de $300)  
**Prós:** Testar gratuitamente por 90 dias, região SP disponível  
**Contras:** Depois volta a $10+/mês

#### 🥉 OPÇÃO 3: Migrar para Cloud SQL
**Custo:** $10.17-28.80/mês  
**Prós:** Integração com Cloud Run, região SP, escalabilidade  
**Contras:** 70-380% mais caro

## 🔧 Se Decidir Migrar Mesmo Assim

Use a configuração mais econômica:

```bash
# Criar instância Cloud SQL mais barata
gcloud sql instances create agenda-cal-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=southamerica-east1 \
  --storage-size=10GB \
  --storage-type=SSD \
  --storage-auto-increase \
  --backup \
  --backup-start-time=03:00 \
  --retained-backups-count=7 \
  --retained-transaction-log-days=7
```

**Custo estimado:** $10.17/mês (+$4/mês vs Render)

---

**Resumo em 3 pontos:**
1. ❌ Cloud SQL é **70% mais caro** que Render para seu uso
2. ✅ **Manter Render** é a opção mais econômica
3. 🎁 Se for novo no GCP, use os **$300 em créditos** para testar gratuitamente

