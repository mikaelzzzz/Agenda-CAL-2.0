import httpx
import json
from typing import Optional
from config import NOTION_DB, HEADERS_NOTION

def notion_find_page(identifier: str | None, by: str = "phone") -> Optional[str]:
    if not identifier:
        return None

    if by == "phone":
        clean_phone = ''.join(filter(str.isdigit, identifier))
        if clean_phone.startswith('55'):
            clean_phone = clean_phone[2:]
        filter_json = {
            "property": "Telefone",
            "phone_number": {"equals": clean_phone}
        }
    elif by == "email":
        filter_json = {
            "property": "Email",
            "email": {"equals": identifier}
        }
    else:
        return None

    print(f"Buscando no Notion com filtro: {json.dumps(filter_json, indent=2)}")

    resp = httpx.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
        headers=HEADERS_NOTION,
        json={"filter": filter_json},
        timeout=15,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])

    if results:
        print(f"Encontrou página no Notion: {results[0]['id']}")
    else:
        print("Nenhuma página encontrada no Notion")

    return results[0]["id"] if results else None


def notion_update_datetime(page_id: str, when: str) -> None:
    print(f"Atualizando Notion page {page_id} com data {when}")
    payload = {
        "properties": {
            "Data Agendada pelo Lead": {
                "rich_text": [{"text": {"content": when}}]
            },
            "Status": {
                "status": {"name": "Agendado reunião"}
            }
        }
    }
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        print(f"Notion atualizado com sucesso: {resp.status_code}")
    except Exception as e:
        print(f"Erro ao atualizar Notion: {str(e)}")
        raise

def notion_update_email(page_id: str, email: str) -> None:
    print(f"Atualizando e-mail da página {page_id} para {email}")
    payload = {
        "properties": {
            "Email": {
                "email": email
            }
        }
    }
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        print(f"E-mail no Notion atualizado com sucesso: {resp.status_code}")
    except Exception as e:
        print(f"Erro ao atualizar e-mail no Notion: {str(e)}")
        # Não levantar exceção para não parar o fluxo principal 