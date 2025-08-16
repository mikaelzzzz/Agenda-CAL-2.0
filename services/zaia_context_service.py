# services/zaia_context_service.py
import httpx
import logging
from typing import Optional

# Configuração de logging consistente com seu padrão
logger = logging.getLogger(__name__)

# Importa as variáveis da Zaia de forma segura
try:
    from config import ZAIA_API_KEY, ZAIA_AGENT_ID, ZAIA_BASE_URL
except ImportError:
    # Se as variáveis não existirem, define valores padrão
    ZAIA_API_KEY = None
    ZAIA_AGENT_ID = None
    ZAIA_BASE_URL = "https://api.zaia.app"

class ZaiaContextService:
    """
    Serviço para enviar mensagens para a Zaia e preservar contexto
    das conversas quando mensagens são enviadas por outros sistemas.
    """
    
    def __init__(self):
        # Valida se as configurações estão disponíveis
        if not ZAIA_API_KEY or not ZAIA_AGENT_ID:
            print("❌ Configurações da Zaia incompletas. Contexto será desabilitado.")
            print(f"   ZAIA_API_KEY: {'✅ Definida' if ZAIA_API_KEY else '❌ Não definida'}")
            print(f"   ZAIA_AGENT_ID: {'✅ Definida' if ZAIA_AGENT_ID else '❌ Não definida'}")
            self.enabled = False
        else:
            self.enabled = True
            self.api_key = ZAIA_API_KEY
            self.agent_id = ZAIA_AGENT_ID
            self.base_url = ZAIA_BASE_URL
            print(f"✅ Serviço de contexto da Zaia inicializado com sucesso")
            print(f"   Agent ID: {self.agent_id}")
            print(f"   Base URL: {self.base_url}")
            print(f"   API Key: {'✅ Configurada' if self.api_key else '❌ Não configurada'}")
    
    def send_message_to_zaia(self, phone: str, message: str, message_type: str = "system") -> bool:
        """
        Envia mensagem para a Zaia para preservar contexto da conversa.
        
        Args:
            phone: Número do telefone
            message: Mensagem completa a ser enviada
            message_type: Tipo da mensagem (system, meeting_confirmation, etc.)
            
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.enabled:
            print("⚠️  Contexto da Zaia desabilitado. Mensagem não enviada.")
            return False
        
        try:
            # Normaliza o telefone usando a mesma função do notion_service
            clean_phone = self._clean_phone_number(phone)
            
            # URL da API da Zaia
            url = f"{self.base_url}/v1.1/api/external-generative-message/create"
            
            # Headers de autenticação
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Payload para a Zaia
            payload = {
                "agentId": int(self.agent_id),
                "externalGenerativeChatExternalId": clean_phone,
                "prompt": f"[SISTEMA] {message}",  # Marca como mensagem do sistema
                "streaming": False,
                "asMarkdown": False,
                "custom": {
                    "whatsapp": clean_phone,
                    "message_type": message_type,
                    "source": "cal_integration"
                }
            }
            
            print(f"📤 Enviando mensagem para Zaia:")
            print(f"   📱 Telefone: {clean_phone}")
            print(f"   🏷️  Tipo: {message_type}")
            print(f"   🌐 URL: {url}")
            print(f"   🔑 Agent ID: {self.agent_id}")
            
            # Faz a requisição para a Zaia usando httpx (consistente com seu padrão)
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, headers=headers, json=payload)
            
            print(f"📡 Resposta da Zaia: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Mensagem enviada para Zaia com sucesso: {message_type}")
                return True
            else:
                print(f"⚠️ Erro ao enviar para Zaia: {response.status_code}")
                print(f"   📄 Resposta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem para Zaia: {e}")
            return False
    
    def send_meeting_confirmation(self, phone: str, message: str) -> bool:
        """Envia especificamente uma confirmação de reunião para a Zaia."""
        return self.send_message_to_zaia(phone, message, "meeting_confirmation")
    
    def send_reminder(self, phone: str, message: str) -> bool:
        """Envia especificamente um lembrete para a Zaia."""
        return self.send_message_to_zaia(phone, message, "reminder")
    
    def send_test_notification(self, phone: str, message: str) -> bool:
        """Envia especificamente uma notificação de teste para a Zaia."""
        return self.send_message_to_zaia(phone, message, "test_notification")
    
    def _clean_phone_number(self, phone: str) -> str:
        """
        Limpa e padroniza o número de telefone para o formato 55...
        Usa a mesma lógica do notion_service para consistência.
        """
        clean_phone = ''.join(filter(str.isdigit, phone))
        if len(clean_phone) > 11 and clean_phone.startswith('55'):
            return clean_phone
        if len(clean_phone) == 11 and not clean_phone.startswith('55'): # Celular de SP sem 55
            return '55' + clean_phone
        if len(clean_phone) == 10 and not clean_phone.startswith('55'): # Celular fora de SP sem 55
             return '55' + clean_phone
        if not clean_phone.startswith('55'):
            return '55' + clean_phone
        return clean_phone