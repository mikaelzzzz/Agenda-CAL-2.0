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

    try:
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
            return results[0]["id"]
        else:
            print("Nenhuma página encontrada no Notion")
            return None
    except Exception as e:
        print(f"Erro ao buscar página no Notion: {e}")
        return None


def notion_update_meeting_date(page_id: str, when: str) -> None:
    """Atualiza apenas a data da reunião na página do Notion."""
    print(f"Atualizando data de reunião da página {page_id} para {when}")
    payload = {
        "properties": {"Data Agendada pelo Lead": {"rich_text": [{"text": {"content": when}}]}}
    }
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        print(f"✓ Data de reunião no Notion atualizada com sucesso.")
    except Exception as e:
        print(f"✗ Erro ao atualizar data de reunião no Notion: {str(e)}")


def notion_update_status(page_id: str, status_name: str) -> None:
    """Atualiza apenas o status na página do Notion."""
    print(f"Atualizando status da página {page_id} para '{status_name}'")
    payload = {
        "properties": {"Status": {"status": {"name": status_name}}}
    }
    try:
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        print(f"✓ Status no Notion atualizado com sucesso.")
    except Exception as e:
        print(f"✗ Erro ao atualizar status no Notion: {str(e)}")


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

def notion_create_page(name: str, email: str | None, phone: str | None) -> str | None:
    """Cria uma nova página no Notion para um novo lead."""
    print(f"Criando nova página no Notion para: {name}")

    properties = {
        "Nome": {
            "title": [{"text": {"content": name}}]
        }
    }
    if email:
        properties["Email"] = {"email": email}
    if phone:
        clean_phone = ''.join(filter(str.isdigit, phone))
        if not clean_phone.startswith('55'):
            clean_phone = '55' + clean_phone
        properties["Telefone"] = {"phone_number": clean_phone}

    payload = {
        "parent": {"database_id": NOTION_DB},
        "properties": properties
    }

    try:
        resp = httpx.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        new_page_id = resp.json()["id"]
        print(f"✓ Nova página criada no Notion com sucesso: {new_page_id}")
        return new_page_id
    except Exception as e:
        print(f"✗ Erro ao criar página no Notion: {str(e)}")
        return None 