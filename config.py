import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Core App Config ---
CAL_SECRET = os.getenv("CAL_SECRET", "changeme").encode()
TZ = pytz.timezone(os.getenv("TZ", "America/Sao_Paulo"))
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Notion API Config ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB = os.getenv("NOTION_DB")
HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2025-09-03",
}

# --- Notion Database Properties ---
# !! IMPORTANTE !!
# Se os nomes das colunas na sua base de dados do Notion forem diferentes,
# ajuste as variáveis de ambiente correspondentes no Render.
NOTION_NAME_PROP = os.getenv("NOTION_NAME_PROP", "Nome")
NOTION_EMAIL_PROP = os.getenv("NOTION_EMAIL_PROP", "Email")
NOTION_PHONE_PROP = os.getenv("NOTION_PHONE_PROP", "Telefone")
NOTION_STATUS_PROP = os.getenv("NOTION_STATUS_PROP", "Status")
NOTION_DATE_PROP = os.getenv("NOTION_DATE_PROP", "Data Agendada pelo Lead")

# --- Notion Status Value ---
# O nome da opção de status que deve ser definida quando uma reunião é agendada.
NOTION_STATUS_VALUE = os.getenv("NOTION_STATUS_VALUE", "Agendado reunião")

# --- Z-API Config ---
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
ADMIN_PHONES = [p.strip() for p in os.getenv("ADMIN_PHONES", "").split(",") if p]

# --- Flexge API Config ---
# Configurações para verificação de testes de nivelamento
FLEXGE_API_KEY = os.getenv("FLEXGE_API_KEY")
FLEXGE_BASE_URL = os.getenv("FLEXGE_BASE_URL", "https://partner-api.flexge.com/external")

# --- Zaia API Config (NOVO) ---
# Configurações para enviar mensagens para a Zaia e preservar contexto
ZAIA_API_KEY = os.getenv("ZAIA_API_KEY")
ZAIA_AGENT_ID = os.getenv("ZAIA_AGENT_ID")
ZAIA_BASE_URL = os.getenv("ZAIA_BASE_URL", "https://api.zaia.app")

# Validação das configurações
if not FLEXGE_API_KEY:
    print("⚠️  AVISO: FLEXGE_API_KEY não configurada. Verificação de testes de nivelamento será desabilitada.")
if not ZAIA_API_KEY:
    print("⚠️  AVISO: ZAIA_API_KEY não configurada. Contexto da Zaia será desabilitado.")
if not ZAIA_AGENT_ID:
    print("⚠️  AVISO: ZAIA_AGENT_ID não configurado. Contexto da Zaia será desabilitado.")