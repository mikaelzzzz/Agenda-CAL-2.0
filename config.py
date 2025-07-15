import os
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CAL_SECRET = os.getenv("CAL_SECRET", "changeme").encode()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB = os.getenv("NOTION_DB")
ZAPI_INSTANCE = os.getenv("ZAPI_INSTANCE")
ZAPI_TOKEN = os.getenv("ZAPI_TOKEN")
ZAPI_CLIENT_TOKEN = os.getenv("ZAPI_CLIENT_TOKEN")
ADMIN_PHONES = [p.strip() for p in os.getenv("ADMIN_PHONES", "").split(",") if p]
TZ = pytz.timezone(os.getenv("TZ", "America/Sao_Paulo"))

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
} 