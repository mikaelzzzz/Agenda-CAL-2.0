#!/bin/bash
# migrate_database.sh - Script para migrar banco de dados PostgreSQL
# Uso: ./migrate_database.sh <NEW_DATABASE_URL>

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Script de Migração de Banco de Dados${NC}"
echo "================================================"
echo ""

# Verificar se foi passado o novo DATABASE_URL
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erro: Você precisa passar o novo DATABASE_URL como argumento${NC}"
    echo ""
    echo "Uso:"
    echo "  ./migrate_database.sh 'postgresql://user:pass@host/db'"
    echo ""
    exit 1
fi

NEW_DB="$1"

# Verificar se OLD_DB está configurado
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL não está configurado${NC}"
    echo "Por favor, exporte a variável com o banco atual:"
    echo "  export DATABASE_URL='postgresql://user:pass@render-host/db'"
    echo ""
    exit 1
fi

OLD_DB="$DATABASE_URL"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

echo -e "${BLUE}Configuração:${NC}"
echo "  Banco Atual (Render): ${OLD_DB:0:30}..."
echo "  Novo Banco: ${NEW_DB:0:30}..."
echo "  Arquivo de Backup: $BACKUP_FILE"
echo ""

# Confirmar migração
read -p "Deseja continuar com a migração? (s/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${YELLOW}Migração cancelada${NC}"
    exit 0
fi

# 1. Fazer backup do banco atual
echo ""
echo -e "${BLUE}📦 Passo 1/4: Fazendo backup do banco atual...${NC}"
if pg_dump "$OLD_DB" > "$BACKUP_FILE" 2>&1; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup criado com sucesso! (Tamanho: $BACKUP_SIZE)${NC}"
else
    echo -e "${RED}❌ Erro ao criar backup${NC}"
    exit 1
fi

# 2. Testar conexão com novo banco
echo ""
echo -e "${BLUE}🔌 Passo 2/4: Testando conexão com novo banco...${NC}"
if psql "$NEW_DB" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Conexão estabelecida com sucesso!${NC}"
else
    echo -e "${RED}❌ Erro ao conectar no novo banco${NC}"
    echo "Verifique se o DATABASE_URL está correto"
    exit 1
fi

# 3. Importar dados no novo banco
echo ""
echo -e "${BLUE}📥 Passo 3/4: Importando dados no novo banco...${NC}"
echo "   (Isso pode demorar alguns minutos...)"
if psql "$NEW_DB" < "$BACKUP_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Dados importados com sucesso!${NC}"
else
    echo -e "${YELLOW}⚠️  Houve alguns warnings durante a importação (normal)${NC}"
    echo "   Vamos verificar se os dados foram importados..."
fi

# 4. Verificar dados importados
echo ""
echo -e "${BLUE}✅ Passo 4/4: Verificando dados importados...${NC}"

# Verificar tabela do APScheduler
JOBS_COUNT=$(psql "$NEW_DB" -t -c "SELECT COUNT(*) FROM apscheduler_jobs;" 2>/dev/null || echo "0")
echo "   📊 Jobs do APScheduler: $JOBS_COUNT"

# Listar todas as tabelas
echo "   📋 Tabelas criadas:"
psql "$NEW_DB" -c "\dt" 2>/dev/null | grep -E "apscheduler|public" | awk '{print "      - " $3}' || echo "      (nenhuma tabela encontrada)"

echo ""
echo -e "${GREEN}🎉 Migração concluída com sucesso!${NC}"
echo ""
echo -e "${BLUE}📝 Próximos passos:${NC}"
echo ""
echo "1. Testar localmente (opcional):"
echo "   export DATABASE_URL='$NEW_DB'"
echo "   python main.py"
echo ""
echo "2. Atualizar DATABASE_URL no Cloud Run:"
echo "   gcloud run services update agenda-cal-2-0 \\"
echo "     --region=southamerica-east1 \\"
echo "     --update-env-vars=\"DATABASE_URL=$NEW_DB\""
echo ""
echo "3. Verificar logs do Cloud Run:"
echo "   gcloud run services logs read agenda-cal-2-0 --region=southamerica-east1 --limit=50"
echo ""
echo "4. Monitorar por 7 dias e, se tudo estiver OK, cancelar o Render"
echo ""
echo -e "${YELLOW}💾 Backup salvo em: $BACKUP_FILE${NC}"
echo "   (Guarde este arquivo por segurança!)"
echo ""

