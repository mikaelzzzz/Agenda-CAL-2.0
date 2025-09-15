# services/placement_test_service.py
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from config import (
    NOTION_TOKEN, NOTION_DB, FLEXGE_API_KEY, FLEXGE_BASE_URL, NOTION_LINK_PROP,
    NOTION_TEST_PROP,
    NOTION_STATUS_PROP, NOTION_IA_ATTENDANCE_PROP, NOTION_EMAIL_PROP, HEADERS_NOTION
)
from services.notion_service import notion_find_page, notion_update_page_property, get_data_source_id

# Nomes das propriedades no Notion
NOTION_LEVEL_PROP = "Nível Flexge"

class PlacementTestService:
    def __init__(self):
        self.api_key = FLEXGE_API_KEY
        self.base_url = FLEXGE_BASE_URL
        self.notion_db = NOTION_DB
        self.enabled = bool(FLEXGE_API_KEY)
        
        if not self.enabled:
            print("⚠️ PlacementTestService desabilitado: FLEXGE_API_KEY não configurada")

    @staticmethod
    def _sanitize_email(raw: str | None) -> str | None:
        """Remove possíveis formatações markdown (ex.: [email](mailto:email)) e espaços."""
        if not raw:
            return raw
        s = raw.strip()
        # Padrão [text](mailto:text)
        if s.startswith("[") and "](mailto:" in s and s.endswith(")"):
            try:
                left = s.find("[")
                right = s.find("](")
                inner = s[left + 1:right]
                return inner.strip()
            except Exception:
                return s
        # Padrão (mailto:email)
        if s.startswith("mailto:"):
            return s.replace("mailto:", "").strip()
        return s
        
    async def get_all_emails_from_notion(self) -> List[str]:
        """Busca todos os emails do database do Notion, aplicando filtros para otimização."""
        try:
            data_source_id = get_data_source_id(self.notion_db)
            if not data_source_id:
                print("❌ data_source_id indisponível para Notion")
                return []
            url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
            headers = HEADERS_NOTION
            
            # Filtros por Status ativos
            filters = {
                "filter": {
                    "or": [
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Em atendimento pela IA"}},
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Qualificado pela IA"}},
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Já entrei em contato"}},
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Agendado reunião"}},
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Reunião Realizada"}},
                        {"property": NOTION_STATUS_PROP, "status": {"equals": "Aguardando resposta"}},
                    ]
                }
            }
            
            all_emails = []
            start_cursor = None
            
            while True:
                payload = {"page_size": 100, **filters}
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                
                results = data.get("results") or []
                if not results:
                    break
                
                for page in results:
                    properties = page.get("properties", {})
                    email_prop = properties.get(NOTION_EMAIL_PROP, {})
                    if email_prop.get("type") == "email" and email_prop.get("email"):
                        all_emails.append(email_prop["email"])
                
                if not data.get("has_more"):
                    break
                start_cursor = data.get("next_cursor")
            
            print(f"✓ Encontrados {len(all_emails)} emails no Notion")
            return all_emails
            
        except Exception as e:
            print(f"❌ Erro ao buscar emails do Notion: {e}")
            return []
    
    async def check_placement_test_status(self, email: str) -> Optional[Dict[str, Any]]:
        """Verifica o status do teste de nivelamento para um email específico, buscando em todas as páginas."""
        try:
            headers = {
                "accept": "application/json",
                "x-api-key": self.api_key
            }
            
            def normalize_email(e: str | None) -> str:
                s = (e or "").strip().lower()
                # Normalização simples para gmail: remove sufixo +tag e pontos na parte local
                if "@gmail.com" in s:
                    local, _, domain = s.partition("@")
                    local = local.split("+")[0].replace(".", "")
                    return f"{local}@{domain}"
                return s
            
            target_email = normalize_email(email)
            
            page = 1
            has_more = True
            next_cursor = None
            pages_visited = 0
            
            async with httpx.AsyncClient() as client:
                while True:
                    params = f"page={page}&sort=createdAt&order=desc"
                    if next_cursor:
                        params += f"&cursor={next_cursor}"
                    url = f"{self.base_url}?{params}"
                    print(f"🔍 Buscando na página {page} (ordem desc) para {email}")
                    
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Suporta formatos { data: [...] } e { docs: [...], total: N }
                    tests = data.get("data")
                    if tests is None:
                        tests = data.get("docs")
                    if tests is None:
                        tests = []
                    
                    if not tests:
                        # Página vazia: encerramos a paginação
                        break
                    pages_visited += 1
                    
                    try:
                        tests = sorted(
                            tests,
                            key=lambda t: (t.get("createdAt") or t.get("updatedAt") or ""),
                            reverse=True,
                        )
                    except Exception:
                        pass
                    
                    # Filtros de consistência
                    def is_completed_valid(t: Dict[str, Any]) -> bool:
                        if t.get("deleted") is True:
                            return False
                        # Alguns payloads não possuem `type`; se houver, validar PLACEMENT
                        t_type = (t.get("type") or "").upper()
                        if t_type and t_type != "PLACEMENT":
                            return False
                        student = t.get("student", {})
                        if student.get("deleted") is True:
                            return False
                        if not t.get("completedAt"):
                            return False
                        return True
                    
                    # 1) Preferir placement-only
                    for test in tests:
                        if not is_completed_valid(test):
                            continue
                        student = test.get("student", {})
                        if normalize_email(student.get("email")) == target_email and student.get("isPlacementTestOnly") is True:
                            print(f"✅ Teste placement-only CONCLUÍDO encontrado para {email} na página {page}")
                            return test
                    
                    # 2) Fallback concluído
                    for test in tests:
                        if not is_completed_valid(test):
                            continue
                        student = test.get("student", {})
                        if normalize_email(student.get("email")) == target_email:
                            print(f"✅ Fallback: teste CONCLUÍDO encontrado para {email} na página {page}")
                            return test
                    
                    # Avança paginação
                    has_more = data.get("has_more") or data.get("hasMore") or False
                    next_cursor = data.get("next_cursor") or data.get("nextCursor")
                    page += 1
                    
                    if not has_more and not next_cursor:
                        # Se não há pistas de continuidade, paramos quando a próxima vier vazia
                        pass
                    
                    if page > 200:
                        print(f"⚠️ Limite de páginas atingido para {email}")
                        break
                    await asyncio.sleep(0.1)
            
            print(f"ℹ️ Nenhum teste CONCLUÍDO encontrado para {email} após verificar {pages_visited} página(s)")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao verificar teste para {email}: {e}")
            return None
    
    async def update_notion_test_status(self, page_id: str, test_data: Optional[Dict[str, Any]]) -> bool:
        """Atualiza o status do teste no Notion."""
        # Observação: a propriedade "Teste de Nivelamento" é do tipo checkbox
        # True = fez o teste | False = não fez (mantemos "Nível Flexge" como "Pendente")
        try:
            if test_data:
                # Aluno fez o teste
                test_status = "Sim"
                
                # Constrói o link do teste usando o ID
                test_id = test_data.get("id")
                if test_id:
                    test_url = f"https://app.flexge.com/placement-tests/{test_id}"
                    # Atualiza o link do teste
                    await notion_update_page_property(
                        page_id, 
                        NOTION_LINK_PROP, 
                        "url", 
                        test_url
                    )
                    print(f"✓ Link do teste atualizado: {test_url}")
                
                # Verifica se tem nível alcançado
                reached_level = test_data.get("reachedLevel", {})
                if reached_level and not reached_level.get("deleted", True):
                    course = reached_level.get("course", {})
                    level_name = course.get("name", "")
                    if level_name:
                        # Atualiza o nível
                        await notion_update_page_property(
                            page_id, 
                            NOTION_LEVEL_PROP, 
                            "rich_text", 
                            [{"text": {"content": level_name}}]
                        )
                        print(f"✓ Nível atualizado para {level_name}")
            else:
                # Aluno não fez o teste
                test_status = "Não"
                # Limpa o link se não fez o teste
                await notion_update_page_property(
                    page_id, 
                    NOTION_LINK_PROP, 
                    "url", 
                    ""
                )
                # Marca nível como Pendente
                await notion_update_page_property(
                    page_id,
                    NOTION_LEVEL_PROP,
                    "rich_text",
                    [{"text": {"content": "Pendente"}}]
                )
            
            # Atualiza a propriedade como checkbox (True para Sim, False para Não)
            await notion_update_page_property(
                page_id,
                NOTION_TEST_PROP,
                "checkbox",
                (test_status == "Sim")
            )

            # Confirma a atualização lendo a página
            try:
                headers = {
                    "Authorization": f"Bearer {NOTION_TOKEN}",
                    "Content-Type": "application/json",
                    "Notion-Version": "2022-06-28",
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    cb = data.get("properties", {}).get(NOTION_TEST_PROP, {}).get("checkbox")
                    expected = (test_status == "Sim")
                    if cb is expected:
                        print(f"✓ Confirmação: '{NOTION_TEST_PROP}' (checkbox) atualizado para {expected}.")
                    else:
                        print(f"⚠️ Aviso: '{NOTION_TEST_PROP}' não refletiu '{expected}' após PATCH. Atual: {cb}")
            except Exception as confirm_err:
                print(f"⚠️ Erro ao confirmar atualização de '{NOTION_TEST_PROP}': {confirm_err}")
            
            print(f"✓ Status do teste atualizado para: {test_status}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao atualizar Notion para {page_id}: {e}")
            return False
    
    async def process_all_students(self) -> None:
        """Processa todos os alunos verificando seus testes de nivelamento."""
        if not self.enabled:
            print("⚠️ PlacementTestService desabilitado. Verificação de testes não executada.")
            return
            
        print("🔄 Iniciando verificação de testes de nivelamento...")
        
        # Busca todos os emails do Notion
        emails = await self.get_all_emails_from_notion()
        if not emails:
            print("⚠️ Nenhum email encontrado no Notion")
            return
        
        print(f"📧 Verificando {len(emails)} emails...")
        
        # Para cada email, verifica o status do teste
        for email in emails:
            try:
                clean_email = self._sanitize_email(email)
                print(f"🔍 Verificando: {clean_email}")
                
                # Busca a página no Notion pelo email
                page_id = notion_find_page(clean_email, "email")
                if not page_id:
                    print(f"⚠️ Página não encontrada para {clean_email}")
                    continue
                
                # Verifica o status do teste
                test_data = await self.check_placement_test_status(clean_email)
                
                # Atualiza o Notion
                await self.update_notion_test_status(page_id, test_data)
                
                # Pequena pausa para não sobrecarregar a API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Erro ao processar {email}: {e}")
                continue
        
        print("✅ Verificação de testes concluída!")

# Instância global do serviço
placement_test_service = PlacementTestService()
