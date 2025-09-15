import httpx
import json
from typing import Optional, Dict, Any
from config import (
    NOTION_DB, HEADERS_NOTION, NOTION_PHONE_PROP, NOTION_EMAIL_PROP,
    NOTION_NAME_PROP, NOTION_STATUS_PROP, NOTION_DATE_PROP
)

# Cache simples para data_source_id
_data_source_cache: Dict[str, str] = {}

def get_data_source_id(database_id: str) -> Optional[str]:
    if database_id in _data_source_cache:
        return _data_source_cache[database_id]
    try:
        resp = httpx.get(
            f"https://api.notion.com/v1/databases/{database_id}",
            headers=HEADERS_NOTION,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        data_sources = data.get("data_sources", [])
        if not data_sources:
            print(f"⚠️ Nenhum data_source para database {database_id}")
            return None
        ds_id = data_sources[0].get("id")
        if ds_id:
            _data_source_cache[database_id] = ds_id
            return ds_id
        return None
    except Exception as e:
        print(f"❌ Erro ao obter data_source_id: {e}")
        return None

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

    data_source_id = get_data_source_id(NOTION_DB)
    if not data_source_id:
        return None

    if by == "phone":
        search_value = clean_phone_number(identifier)
        filter_json = {"property": NOTION_PHONE_PROP, "phone_number": {"equals": search_value}}
    elif by == "email":
        filter_json = {"property": NOTION_EMAIL_PROP, "email": {"equals": identifier}}
    else:
        return None

    print(f"Buscando no Notion com filtro: {json.dumps(filter_json, indent=2)}")

    try:
        resp = httpx.post(
            f"https://api.notion.com/v1/data_sources/{data_source_id}/query",
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

    data_source_id = get_data_source_id(NOTION_DB)
    if not data_source_id:
        print("❌ data_source_id indisponível")
        return None

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
        "parent": {"type": "data_source_id", "data_source_id": data_source_id},
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
        print(f"Payload enviado: {json.dumps(payload, indent=2)}")
        return None

async def notion_update_page_property(page_id: str, property_name: str, property_type: str, value: any) -> bool:
    """Atualiza uma propriedade específica de uma página no Notion."""
    try:
        # Constrói o payload baseado no tipo da propriedade
        if property_type == "url":
            property_value = value if value else None
        elif property_type == "select":
            property_value = value
        elif property_type == "rich_text":
            property_value = value
        else:
            property_value = value
        
        payload = {
            "properties": {
                property_name: {
                    property_type: property_value
                }
            }
        }
        
        resp = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar propriedade {property_name} no Notion: {e}")
        return False 

def get_database_properties() -> Dict[str, Any] | None:
    """Obtém o schema (properties) do database no Notion."""
    try:
        resp = httpx.get(
            f"https://api.notion.com/v1/databases/{NOTION_DB}",
            headers=HEADERS_NOTION,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("properties", {})
    except Exception as e:
        print(f"❌ Erro ao obter schema do database: {e}")
        return None

def ensure_multi_select_options(property_name: str, desired_names: list[str]) -> Dict[str, str]:
    """Garante que as opções informadas existam na propriedade multi_select.
    Retorna um mapa nome->id das opções solicitadas (criando-as se necessário).
    """
    properties = get_database_properties()
    if properties is None:
        return {}

    prop = properties.get(property_name)
    if not prop:
        print(f"❌ Propriedade '{property_name}' não encontrada no database")
        return {}

    if prop.get("type") != "multi_select":
        print(f"❌ Propriedade '{property_name}' não é do tipo multi_select (é {prop.get('type')})")
        return {}

    options = prop.get("multi_select", {}).get("options", [])
    name_to_id: Dict[str, str] = {opt.get("name"): opt.get("id") for opt in options if opt.get("name") and opt.get("id")}

    missing = [n for n in desired_names if n not in name_to_id]
    if missing:
        updated_options = options + [{"name": n} for n in missing]
        payload = {
            "properties": {
                property_name: {
                    "multi_select": {
                        "options": updated_options
                    }
                }
            }
        }
        try:
            resp = httpx.patch(
                f"https://api.notion.com/v1/databases/{NOTION_DB}",
                headers=HEADERS_NOTION,
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            properties = get_database_properties() or {}
            prop = properties.get(property_name, {})
            options = prop.get("multi_select", {}).get("options", [])
            name_to_id = {opt.get("name"): opt.get("id") for opt in options if opt.get("name") and opt.get("id")}
            print(f"✓ Opções adicionadas à propriedade '{property_name}': {', '.join(missing)}")
        except Exception as e:
            print(f"❌ Erro ao atualizar opções da propriedade '{property_name}': {e}")

    return {name: name_to_id.get(name) for name in desired_names if name in name_to_id}