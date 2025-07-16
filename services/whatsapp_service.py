import requests
import json
from datetime import datetime
from config import ZAPI_CLIENT_TOKEN, ZAPI_INSTANCE, ZAPI_TOKEN, ADMIN_PHONES
from utils import format_pt_br

def send_wa_message(phone: str, message: str, has_link: bool = False, link_data: dict | None = None) -> None:
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
            
        response.raise_for_status()
    except Exception as e:
        print(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
        raise

def send_wa_bulk(message: str) -> None:
    for phone in ADMIN_PHONES:
        send_wa_message(phone, message)

def send_immediate_booking_notifications(
    attendee_name: str,
    whatsapp: str | None,
    start_dt: datetime,
) -> None:
    """Envia três mensagens separadas: confirmação + Zoom, teste, vídeo."""
    zoom_url = (
        "https://us06web.zoom.us/j/8902841864?"
        "pwd=OIjXN37C7fjELriVg4y387EbXUSVsR.1"
    )

    # 1️⃣ confirmação + link do Zoom
    msg1 = (
        f"Pronto, {attendee_name}!!\n\n"
        f"✅ Sua reunião está confirmada para *{start_dt.strftime('%d/%m')}* "
        f"às *{start_dt.strftime('%H:%M')}*.\n\n"
        "🖥️ Acesse a sala da reunião no link abaixo 👇\n"
        f"{zoom_url}"
    )

    # 2️⃣ link do teste de nivelamento
    msg2 = (
        "Antes disso, que tal fazer nosso teste de nivelamento?\n"
        "👉 https://student.flexge.com/v2/placement/karoleloi\n"
        "Faça o teste sem pressa, no seu tempo, ok? 😉"
    )

    # 3️⃣ link do vídeo sobre o método
    msg3 = (
        "Aproveite e assista a este vídeo para entender por que nosso método "
        "é diferenciado!\n"
        "👉 https://www.youtube.com/watch?v=fKepCx3lMZI"
    )

    if whatsapp:
        # Envia cada mensagem individualmente
        send_wa_message(whatsapp, msg1)
        send_wa_message(whatsapp, msg2)
        send_wa_message(whatsapp, msg3)

    # ------------------------------------------------------------------
    # Mensagem para o time de vendas continua igual
    formatted_pt = format_pt_br(start_dt)
    sales_message = (
        "💼 Nova Reunião Agendada!\n\n"
        f"👤 Cliente: {attendee_name}\n"
        f"📅 Data: {formatted_pt}"
    )
    for admin_phone in ADMIN_PHONES:
        send_wa_message(admin_phone, sales_message) 