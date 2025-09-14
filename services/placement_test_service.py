# services/placement_test_service.py
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from config import NOTION_TOKEN, NOTION_DB, FLEXGE_API_KEY, FLEXGE_BASE_URL, NOTION_LINK_PROP
from services.notion_service import notion_find_page, notion_update_page_property

# Nomes das propriedades no Notion
NOTION_EMAIL_PROP = "Email"
NOTION_TEST_PROP = "Já fez o teste de nivelamento?"
NOTION_LEVEL_PROP = "Nível Flexge"

class PlacementTestService:
    def __init__(self):
        self.api_key = FLEXGE_API_KEY
        self.base_url = FLEXGE_BASE_URL
        self.notion_db = NOTION_DB
        self.enabled = bool(FLEXGE_API_KEY)
        
        if not self.enabled:
            print("⚠️ PlacementTestService desabilitado: FLEXGE_API_KEY não configurada")
        
    async def get_all_emails_from_notion(self) -> List[str]:
        """Busca todos os emails do database do Notion."""
        try:
            # Primeiro descobre o data_source_id
            from services.notion_service import get_data_source_id
            data_source_id = get_data_source_id(self.notion_db)
            if not data_source_id:
                print("❌ Não foi possível descobrir data_source_id")
                return []
            
            # Busca todas as páginas do data source
            url = f"https://api.notion.com/v1/data_sources/{data_source_id}/query"
            headers = {
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": "2025-09-03"
            }
            
            all_emails = []
            has_more = True
            start_cursor = None
            
            while has_more:
                payload = {
                    "page_size": 100
                }
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()
                
                # Extrai emails das páginas
                for page in data.get("results", []):
                    properties = page.get("properties", {})
                    email_prop = properties.get(NOTION_EMAIL_PROP, {})
                    
                    if email_prop.get("type") == "email" and email_prop.get("email"):
                        all_emails.append(email_prop["email"])
                
                has_more = data.get("has_more", False)
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
            
            page = 1
            has_more = True
            
            async with httpx.AsyncClient() as client:
                while has_more:
                    url = f"{self.base_url}/placement-tests?page={page}"
                    print(f"🔍 Buscando na página {page} para {email}")
                    
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Procura pelo email nos resultados da página atual
                    for test in data.get("data", []):
                        student = test.get("student", {})
                        if student.get("email") == email:
                            print(f"✅ Teste encontrado para {email} na página {page}")
                            return test
                    
                    # Verifica se há mais páginas
                    has_more = data.get("has_more", False)
                    page += 1
                    
                    # Limite de segurança para evitar loop infinito
                    if page > 100:  # Máximo 100 páginas
                        print(f"⚠️ Limite de páginas atingido para {email}")
                        break
                    
                    # Pequena pausa entre requisições para não sobrecarregar a API
                    await asyncio.sleep(0.1)
            
            print(f"ℹ️ Nenhum teste encontrado para {email} em {page-1} páginas")
            return None
            
        except Exception as e:
            print(f"❌ Erro ao verificar teste para {email}: {e}")
            return None
    
    async def update_notion_test_status(self, page_id: str, test_data: Optional[Dict[str, Any]]) -> bool:
        """Atualiza o status do teste no Notion."""
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
            
            # Atualiza o status do teste
            await notion_update_page_property(
                page_id, 
                NOTION_TEST_PROP, 
                "select", 
                {"name": test_status}
            )
            
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
                print(f"🔍 Verificando: {email}")
                
                # Busca a página no Notion pelo email
                page = await notion_find_page(email, "email")
                if not page:
                    print(f"⚠️ Página não encontrada para {email}")
                    continue
                
                page_id = page["id"]
                
                # Verifica o status do teste
                test_data = await self.check_placement_test_status(email)
                
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
