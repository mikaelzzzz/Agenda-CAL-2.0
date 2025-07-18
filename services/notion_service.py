import httpx
import json
from typing import Optional
from config import (
    NOTION_DB, HEADERS_NOTION, NOTION_PHONE_PROP, NOTION_EMAIL_PROP,
    NOTION_NAME_PROP, NOTION_STATUS_PROP, NOTION_DATE_PROP
)

def clean_phone_number(phone: str) -> str:
    """Limpa e padroniza o número de telefone para o formato 55..."""
    clean_phone = ''.join(filter(str.isdigit, phone))
    if len(clean_phone) > 11 and clean_phone.startswith('55'):
        return clean_phone
    if len(clean_phone) == 11 and not clean_phone.startswith('55'): # Celular de SP sem 55
        return '55' + clean_phone
    if len(clean_phone) == 10 and not clean_phone.startswith('55'): # Celular fora de SP sem 55
         return '55' + clean_phone # A Z-API pode lidar com isso, mas vamos padronizar
    # Adicionar outras regras se necessário
    if not clean_phone.startswith('55'):
        return '55' + clean_phone
    return clean_phone

def notion_find_page(identifier: str | None, by: str = "phone") -> Optional[str]:
    if not identifier:
        return None

    if by == "phone":
        # CORREÇÃO: Busca pelo número completo com '55', sem remover.
        search_value = clean_phone_number(identifier)
        filter_json = {"property": NOTION_PHONE_PROP, "phone_number": {"equals": search_value}}
    elif by == "email":
        filter_json = {"property": NOTION_EMAIL_PROP, "email": {"equals": identifier}}
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
        "properties": {NOTION_DATE_PROP: {"rich_text": [{"text": {"content": when}}]}}
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
        "properties": {NOTION_STATUS_PROP: {"status": {"name": status_name}}}
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
            NOTION_EMAIL_PROP: {
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

def notion_create_page(
    name: str,
    email: str | None,
    phone: str | None,
    meeting_date: str,
    status: str
) -> str | None:
    """Cria uma nova página no Notion para um novo lead com todos os detalhes."""
    print(f"Criando nova página no Notion para: {name}")

    properties = {
        NOTION_NAME_PROP: {"title": [{"text": {"content": name}}]},
        NOTION_STATUS_PROP: {"status": {"name": status}},
        NOTION_DATE_PROP: {"rich_text": [{"text": {"content": meeting_date}}]},
    }
    if email:
        properties[NOTION_EMAIL_PROP] = {"email": email}
    if phone:
        properties[NOTION_PHONE_PROP] = {"phone_number": clean_phone_number(phone)}

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
        # Adiciona log do payload para depuração
        print(f"Payload enviado: {json.dumps(payload, indent=2)}")
        return None 