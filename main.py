from __future__ import annotations
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, Header, HTTPException, Request, status, Body
from pydantic import ValidationError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

from config import CAL_SECRET, TZ, ADMIN_PHONES, HEADERS_NOTION, NOTION_DB
from models import (
    CalWebhookPayload,
    ScheduleTestRequest,
    ScheduleLeadTestRequest,
    SendLeadMessageRequest,
)
from services.notion_service import notion_find_page, notion_update_datetime, notion_update_email
from services.whatsapp_service import send_immediate_booking_notifications, send_wa_message
from services.scheduling_service import schedule_messages, schedule_lead_messages
from utils import format_pt_br

# -----------------------------------------------------------------------------
# FastAPI app & scheduler
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Cal.com → Notion + WhatsApp Integration",
    description="Integration service that receives Cal.com webhooks and syncs with Notion and WhatsApp",
    version="1.0.1"
)

scheduler = AsyncIOScheduler()
scheduler.start()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def verify_signature(signature_header: str | None, raw_body: bytes) -> None:
    if not signature_header:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature")

    digest = hmac.new(CAL_SECRET, raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature_header):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

# -----------------------------------------------------------------------------
# Webhook endpoint
# -----------------------------------------------------------------------------
@app.post("/webhook/cal")
async def cal_webhook(
    request: Request, x_cal_signature_256: str = Header(None)
):
    print("\n=== Novo webhook recebido ===")
    print(f"Signature: {x_cal_signature_256}")
    
    raw_body = await request.body()
    try:
        verify_signature(x_cal_signature_256, raw_body)
        print("✓ Assinatura verificada com sucesso")
    except Exception as e:
        print(f"✗ Erro na verificação da assinatura: {str(e)}")
        raise

    print("\nPayload recebido do Cal.com:")
    payload_json = json.loads(raw_body)
    print(json.dumps(payload_json, indent=2))

    try:
        data = CalWebhookPayload.model_validate_json(raw_body)
        print("✓ Payload validado com sucesso")
    except ValidationError as e:
        print("✗ Erro de validação:")
        print(e.json())
        raise HTTPException(
            status_code=400,
            detail=f"Payload inválido: {str(e)}"
        )

    print(f"\nTipo de evento: {data.trigger_event}")
    if data.trigger_event not in {"BOOKING_CREATED", "BOOKING_RESCHEDULED", "BOOKING_REQUESTED"}:
        print(f"Evento ignorado: {data.trigger_event}")
        return {"ignored": data.trigger_event}

    attendee = data.payload.attendees[0]
    start_iso = data.payload.start_time
    start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00")).astimezone(TZ)
    formatted_pt = format_pt_br(start_dt)

    print(f"\nDetalhes do agendamento:")
    print(f"Nome: {attendee.name}")
    print(f"Email: {attendee.email}")
    print(f"Data: {formatted_pt}")

    # 1. Extrair WhatsApp do payload
    whatsapp = None
    ufr = data.payload.userFieldsResponses
    if ufr and ufr.Whatsapp and 'value' in ufr.Whatsapp:
        whatsapp = ufr.Whatsapp['value']

    if not whatsapp:
        resp_field = getattr(data.payload, 'responses', None)
        if resp_field and isinstance(resp_field, dict) and 'whatsapp' in resp_field:
             whatsapp = resp_field['whatsapp'].get('value')
    
    if whatsapp:
        print(f"WhatsApp extraído do payload: {whatsapp}")

    # 2. Encontrar a página no Notion
    page_id = None
    # Prioridade 1: Buscar pelo número de WhatsApp
    if whatsapp:
        page_id = notion_find_page(whatsapp, by="phone")

    # Prioridade 2: Se não encontrou por telefone, buscar por e-mail
    if not page_id and attendee.email:
        print(f"Não encontrou por telefone. Tentando por e-mail: {attendee.email}")
        page_id = notion_find_page(attendee.email, by="email")

    # 3. Se encontrou a página, garantir que temos o número de WhatsApp
    if page_id and not whatsapp:
        try:
            resp = httpx.get(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS_NOTION)
            resp.raise_for_status()
            page_props = resp.json().get("properties", {})
            if "Telefone" in page_props and page_props["Telefone"].get("phone_number"):
                whatsapp = page_props["Telefone"]["phone_number"]
                print(f"WhatsApp encontrado na página do Notion: {whatsapp}")
        except Exception as e:
            print(f"Erro ao buscar telefone do Notion pela página: {e}")

    # 4. Atualizar Notion e enviar notificações
    if page_id:
        print(f"Página do Notion encontrada: {page_id}")
        try:
            notion_update_datetime(page_id, formatted_pt)
            if attendee.email:
                notion_update_email(page_id, attendee.email)
        except Exception as e:
            print(f"✗ Erro na atualização do Notion: {str(e)}")
    else:
        print("✗ Página não encontrada no Notion, nem por telefone nem por e-mail.")

    # Enviar notificações e agendar mensagens
    try:
        print("\nEnviando notificações imediatas...")
        send_immediate_booking_notifications(attendee.name, whatsapp, start_dt)
        print("✓ Notificações imediatas enviadas com sucesso")

        print("\nAgendando mensagens futuras...")
        if whatsapp:
            schedule_lead_messages(scheduler, attendee.name, whatsapp, start_dt)
            print("✓ Mensagens futuras para o lead agendadas com sucesso.")
        
        # Mantem o agendamento para os admins
        schedule_messages(scheduler, attendee.name, start_dt)
        print("✓ Mensagens futuras para admins agendadas com sucesso")

    except Exception as e:
        print(f"✗ Erro no envio ou agendamento de mensagens: {str(e)}")
    
    print("\n=== Webhook processado com sucesso ===")
    return {"success": True}

# -----------------------------------------------------------------------------
# Health check & Test endpoints
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "version": "1.0.1",
        "timezone": str(TZ),
        "admin_phones_configured": len(ADMIN_PHONES),
    }

@app.post("/test/schedule-messages", tags=["Testes"])
def test_schedule_messages(req: ScheduleTestRequest = Body(...)):
    """Agende mensagens futuras para teste (admins)."""
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        schedule_messages(scheduler, req.first_name, dt)
        return {"success": True, "scheduled_for": req.meeting_datetime}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/test/schedule-lead-messages", tags=["Testes"])
def test_schedule_lead_messages(req: ScheduleLeadTestRequest = Body(...)):
    """Agende mensagens futuras para um lead (buscando telefone pelo e-mail no Notion)."""
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        page_id = notion_find_page(req.email, by="email")
        if not page_id:
            return {"success": False, "error": "Lead não encontrado no Notion"}
        
        resp = httpx.get(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=HEADERS_NOTION,
            timeout=15,
        )
        resp.raise_for_status()
        page = resp.json()
        phone = None
        props = page.get("properties", {})
        if "Telefone" in props and props["Telefone"].get("phone_number"):
            phone = props["Telefone"]["phone_number"]
        
        if not phone:
            return {"success": False, "error": "Telefone não encontrado para o lead no Notion"}
        
        schedule_lead_messages(scheduler, req.first_name, phone, dt)
        return {"success": True, "scheduled_for": req.meeting_datetime, "phone": phone}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/test/send-lead-message", tags=["Testes"])
def test_send_lead_message(req: SendLeadMessageRequest = Body(...)):
    """Envie ou agende uma mensagem específica para o lead (buscando telefone pelo e-mail no Notion)."""
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        page_id = notion_find_page(req.email, by="email")
        if not page_id:
            return {"success": False, "error": "Lead não encontrado no Notion"}

        resp = httpx.get(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS_NOTION, timeout=15)
        resp.raise_for_status()
        page = resp.json()
        phone = None
        props = page.get("properties", {})
        if "Telefone" in props and props["Telefone"].get("phone_number"):
            phone = props["Telefone"]["phone_number"]

        if not phone:
            return {"success": False, "error": "Telefone não encontrado para o lead no Notion"}

        meeting_str = dt.strftime("%H:%M")
        if req.which == "1d":
            msg = f"Olá {req.first_name}, amanhã temos nossa reunião às {meeting_str}. Estamos ansiosos para falar com você!"
            when = dt - timedelta(days=1)
        elif req.which == "4h":
            msg = f"Oi {req.first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?"
            when = dt - timedelta(hours=4)
        elif req.which == "after":
            msg = f"{req.first_name}, obrigado pela reunião! Qualquer dúvida, estamos à disposição."
            when = dt + timedelta(hours=1)
        else:
            return {"success": False, "error": "Tipo de mensagem inválido. Use: 1d, 4h ou after."}
        
        if req.send_now:
            send_wa_message(phone, msg)
            return {"success": True, "sent_now": True, "phone": phone, "message": msg}
        else:
            scheduler.add_job(
                send_wa_message,
                trigger=DateTrigger(run_date=when),
                args=[phone, msg],
                id=f"lead_whatsapp_{dt.timestamp()}_{req.which}",
                replace_existing=True,
            )
            return {"success": True, "scheduled_for": when.isoformat(), "phone": phone, "message": msg}
    except Exception as e:
        return {"success": False, "error": str(e)} 