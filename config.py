import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Core App Config ---
CAL_SECRET = os.getenv("CAL_SECRET", "changeme").encode()
TZ = pytz.timezone(os.getenv("TZ", "America/Sao_Paulo"))

# --- Notion API Config ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB = os.getenv("NOTION_DB")
HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
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