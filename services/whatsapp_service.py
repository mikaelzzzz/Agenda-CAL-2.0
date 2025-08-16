import requests
import json
from datetime import datetime
from config import ZAPI_CLIENT_TOKEN, ZAPI_INSTANCE, ZAPI_TOKEN, ADMIN_PHONES
from utils import format_pt_br
from services.zaia_context_service import ZaiaContextService

# URL do webhook para marcar mensagens do sistema
# ✅ CORRIGIDO: URL corrigida para o serviço correto
WEBHOOK_URL = "https://agenda-cal-2-0.onrender.com/webhook"

# Inicializa o serviço de contexto da Zaia
zaia_context = ZaiaContextService()

def mark_system_message(phone: str, message_type: str):
    """
    Marca mensagem do sistema para evitar perda de contexto no agente da Zaia.
    """
    try:
        # Normaliza o telefone
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        if not clean_phone.startswith('55'):
            clean_phone = '55' + clean_phone
        
        webhook_data = {
            "type": "system_message_sent",
            "phone": clean_phone,
            "message_type": message_type
        }
        
        # ✅ MELHORADO: Tratamento de erro mais robusto
        try:
            response = requests.post(WEBHOOK_URL, json=webhook_data, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Contexto marcado para {clean_phone}: {message_type}")
                return True
            else:
                print(f"⚠️ Erro ao marcar contexto: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Erro de conexão ao marcar contexto: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao marcar contexto: {e}")
        return False

def send_wa_message(phone: str, message: str, has_link: bool = False, link_data: dict | None = None, message_type: str = "system") -> None:
    """Send a WhatsApp message using Z-API."""
    # Limpar o número de telefone (remover caracteres não numéricos)
    clean_phone = ''.join(filter(str.isdigit, phone))
    # Garantir que comece com 55 (Brasil)
    if not clean_phone.startswith('55'):
        clean_phone = '55' + clean_phone
    
    print(f"Enviando mensagem WhatsApp para {clean_phone}")
    print(f"Conteúdo da mensagem: {message}")
    
    headers = {
        "Client-Token": ZAPI_CLIENT_TOKEN,
        "Content-Type": "application/json"
    }
    
    base_url = f"https://api.z-api.io/instances/{ZAPI_INSTANCE}/token/{ZAPI_TOKEN}"
    
    # Se tiver link, usar o endpoint de send-link
    if has_link and link_data:
        url = f"{base_url}/send-link"
        payload = {
            "phone": clean_phone,
            "message": message,
            "image": link_data.get("image"),  # Optional
            "linkUrl": link_data["url"],
            "title": link_data["title"],
            "linkDescription": link_data["description"],
            "linkType": "LARGE"  # Use LARGE para melhor visualização
        }
        print(f"Enviando link com payload: {json.dumps(payload, indent=2)}")
    else:
        # Tentar endpoint /send-text
        url = f"{base_url}/send-text"
        payload = {
            "phone": clean_phone,
            "message": message
        }
        print(f"Enviando texto com payload: {json.dumps(payload, indent=2)}")
    
    print(f"URL da requisição: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_text = response.text
        print(f"Status code: {response.status_code}")
        print(f"Resposta Z-API: {response_text}")
        
        if response.status_code != 200 or "error" in response_text.lower():
            print("Erro detectado na resposta!")
            print(f"Headers enviados: {json.dumps(headers, indent=2)}")
        else:
            print("Mensagem enviada com sucesso!")
            
            # Envia para a Zaia para preservar contexto
            if message_type != "admin":  # Não envia contexto para mensagens administrativas
                zaia_context.send_message_to_zaia(clean_phone, message, message_type)
            
            # ✅ CORRIGIDO: Só marca no contexto para mensagens imediatas, não para lembretes agendados
            if message_type not in ["admin", "reminder"]:  # Não marca mensagens para admins nem lembretes
                mark_system_message(clean_phone, message_type)
            
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
        raise

def send_wa_bulk(message: str) -> None:
    for phone in ADMIN_PHONES:
        send_wa_message(phone, message, message_type="admin")

def send_immediate_booking_notifications(
    attendee_name: str,
    whatsapp: str | None,
    start_dt: datetime,
) -> None:
    """Envia a mensagem de confirmação imediata com o teste de nivelamento."""
    first_name = attendee_name.split(' ')[0]
    zoom_url = (
        "https://us06web.zoom.us/j/8902841864?"
        "pwd=OIjXN37C7fjELriVg4y387EbXUSVsR.1"
    )

    # Mensagem combinada: confirmação + teste de nivelamento + Zoom
    confirmation_message = (
        f"Pronto, {first_name}!!\n\n"
        f"✅ Sua reunião está confirmada para *{start_dt.strftime('%d/%m')}* "
        f"às *{start_dt.strftime('%H:%M')}*.\n\n"
        "📝 Acesse aqui o seu teste de nivelamento: https://student.flexge.com/v2/placement/karoleloi\n\n"
        "🖥️ Acesse a sala da reunião no link abaixo 👇\n"
        "https://zoom.us/j/8902841864"
    )

    if whatsapp:
        # Envia a mensagem combinada e marca como confirmação de reunião
        send_wa_message(whatsapp, confirmation_message, message_type="meeting_confirmation")

    # ------------------------------------------------------------------
    # Mensagem para o time de vendas continua igual (com nome completo)
    formatted_pt = format_pt_br(start_dt)
    sales_message = (
        "�� Nova Reunião Agendada!\n\n"
        f"�� Cliente: {attendee_name}\n"
        f"📅 Data: {formatted_pt}"
    )
    for admin_phone in ADMIN_PHONES:
        send_wa_message(admin_phone, sales_message, message_type="admin")