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

from config import CAL_SECRET, TZ, ADMIN_PHONES, HEADERS_NOTION, NOTION_STATUS_VALUE
from models import (
    CalWebhookPayload,
    ScheduleTestRequest,
    ScheduleLeadTestRequest,
    SendLeadMessageRequest,
)
from services.notion_service import (
    notion_find_page,
    notion_update_meeting_date,
    notion_update_status,
    notion_update_email,
    notion_create_page
)
from services.whatsapp_service import send_immediate_booking_notifications, send_wa_message
from services.scheduling_service import schedule_messages, schedule_lead_messages
from utils import format_pt_br

# -----------------------------------------------------------------------------
# FastAPI app & scheduler
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Cal.com → Notion + WhatsApp Integration",
    description="Integration service that receives Cal.com webhooks and syncs with Notion and WhatsApp",
    version="1.0.3"
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
    raw_body = await request.body()
    # verify_signature(x_cal_signature_256, raw_body) # Temporariamente desabilitado para testes
    
    print("\nPayload recebido do Cal.com:")
    payload_json = json.loads(raw_body)
    print(json.dumps(payload_json, indent=2))

    try:
        data = CalWebhookPayload.model_validate_json(raw_body)
    except ValidationError as e:
        print(f"✗ Erro de validação: {e.json()}")
        raise HTTPException(status_code=400,detail=f"Payload inválido: {str(e)}")

    if data.trigger_event not in {"BOOKING_CREATED", "BOOKING_RESCHEDULED", "BOOKING_REQUESTED"}:
        return {"ignored": data.trigger_event}

    attendee = data.payload.attendees[0]
    start_dt = datetime.fromisoformat(data.payload.start_time.replace("Z", "+00:00")).astimezone(TZ)
    formatted_pt = format_pt_br(start_dt)

    print(f"\nDetalhes do agendamento: Nome: {attendee.name}, Email: {attendee.email}, Data: {formatted_pt}")

    # 1. Extrair WhatsApp do payload
    whatsapp = None
    ufr = data.payload.userFieldsResponses
    if ufr and ufr.WhatsApp and 'value' in ufr.WhatsApp:
        whatsapp = ufr.WhatsApp['value']
    
    if whatsapp:
        print(f"WhatsApp extraído do payload: {whatsapp}")

    # 2. Encontrar ou criar página no Notion
    page_id = None
    if whatsapp:
        page_id = notion_find_page(whatsapp, by="phone")
    if not page_id and attendee.email:
        page_id = notion_find_page(attendee.email, by="email")

    if page_id:
        print(f"Página do Notion encontrada: {page_id}")
        notion_update_meeting_date(page_id, formatted_pt)
        notion_update_status(page_id, NOTION_STATUS_VALUE)
        if attendee.email:
            notion_update_email(page_id, attendee.email)
    else:
        print("Lead não encontrado. Criando novo registro no Notion...")
        page_id = notion_create_page(
            name=attendee.name,
            email=attendee.email,
            phone=whatsapp,
            meeting_date=formatted_pt,
            status=NOTION_STATUS_VALUE
        )

    # Enviar notificações e agendar mensagens
    if not page_id:
        print("✗ Não foi possível encontrar ou criar uma página no Notion. O fluxo de notificação para o lead pode não funcionar.")
    
    if whatsapp:
        send_immediate_booking_notifications(attendee.name, whatsapp, start_dt)
        schedule_lead_messages(scheduler, attendee.name, whatsapp, start_dt)
        print("✓ Notificações para o lead enviadas e agendadas.")

    # Notificações para admins
    schedule_messages(scheduler, attendee.name, start_dt)
    print("✓ Lembretes para admins agendados.")

    return {"success": True}

# -----------------------------------------------------------------------------
# Health check & Test endpoints
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "version": "1.0.3",
        "timezone": str(TZ),
        "admin_phones_configured": len(ADMIN_PHONES),
    }

@app.post("/test/schedule-messages", tags=["Testes"])
def test_schedule_messages(req: ScheduleTestRequest = Body(...)):
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        schedule_messages(scheduler, req.first_name, dt)
        return {"success": True, "scheduled_for": req.meeting_datetime}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/test/schedule-lead-messages", tags=["Testes"])
def test_schedule_lead_messages(req: ScheduleLeadTestRequest = Body(...)):
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        page_id = notion_find_page(req.email, by="email")
        if not page_id:
            return {"success": False, "error": "Lead não encontrado no Notion"}
        
        resp = httpx.get(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS_NOTION)
        resp.raise_for_status()
        page_props = resp.json().get("properties", {})
        phone = page_props.get("Telefone", {}).get("phone_number")
        
        if not phone:
            return {"success": False, "error": "Telefone não encontrado para o lead no Notion"}
        
        schedule_lead_messages(scheduler, req.first_name, phone, dt)
        return {"success": True, "scheduled_for": req.meeting_datetime, "phone": phone}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/test/send-lead-message", tags=["Testes"])
def test_send_lead_message(req: SendLeadMessageRequest = Body(...)):
    try:
        dt = datetime.fromisoformat(req.meeting_datetime)
        page_id = notion_find_page(req.email, by="email")
        if not page_id:
            return {"success": False, "error": "Lead não encontrado no Notion"}

        resp = httpx.get(f"https://api.notion.com/v1/pages/{page_id}", headers=HEADERS_NOTION)
        resp.raise_for_status()
        page_props = resp.json().get("properties", {})
        phone = page_props.get("Telefone", {}).get("phone_number")

        if not phone:
            return {"success": False, "error": "Telefone não encontrado para o lead no Notion"}

        meeting_str = dt.strftime("%H:%M")
        if req.which == "1d":
            msg = f"Olá {req.first_name}, amanhã temos nossa reunião às {meeting_str}. Ansiosos para falar com você!"
        elif req.which == "4h":
            msg = f"Oi {req.first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?"
        elif req.which == "after":
            msg = f"{req.first_name}, obrigado pela reunião! Qualquer dúvida, estamos à disposição."
        else:
            return {"success": False, "error": "Tipo de mensagem inválido. Use: 1d, 4h ou after."}
        
        when = {"1d": dt - timedelta(days=1), "4h": dt - timedelta(hours=4), "after": dt + timedelta(hours=1)}[req.which]

        if req.send_now:
            send_wa_message(phone, msg)
            return {"success": True, "sent_now": True, "phone": phone, "message": msg}
        else:
            scheduler.add_job(send_wa_message, trigger=DateTrigger(run_date=when), args=[phone, msg], id=f"lead_whatsapp_{dt.timestamp()}_{req.which}", replace_existing=True)
            return {"success": True, "scheduled_for": when.isoformat(), "phone": phone, "message": msg}
    except Exception as e:
        return {"success": False, "error": str(e)} 