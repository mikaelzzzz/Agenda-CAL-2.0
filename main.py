from __future__ import annotations
from contextlib import asynccontextmanager
import hmac
import hashlib
import json
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, Header, HTTPException, Request, status, Body
from pydantic import ValidationError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import CAL_SECRET, TZ, ADMIN_PHONES, HEADERS_NOTION, NOTION_STATUS_VALUE, DATABASE_URL
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

# NOVA IMPORTAÇÃO: Serviço de contexto da Zaia
from services.zaia_context_service import ZaiaContextService

# NOVA IMPORTAÇÃO: Serviço de verificação de testes de nivelamento
from services.placement_test_service import placement_test_service

# -----------------------------------------------------------------------------
# Scheduler Setup with Persistent Job Store
# -----------------------------------------------------------------------------
jobstores = {
    'default': SQLAlchemyJobStore(url=DATABASE_URL)
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

# ✅ REMOVIDO: Inicialização duplicada do ZaiaContextService
# O serviço será inicializado apenas quando necessário em whatsapp_service.py

# -----------------------------------------------------------------------------
# FastAPI app & scheduler lifecycle
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Iniciar o scheduler quando a aplicação iniciar
    scheduler.start()
    print("Scheduler started...")
    
    # ✅ NOVO: Adicionar job periódico para verificar testes de nivelamento
    scheduler.add_job(
        placement_test_service.process_all_students,
        trigger=IntervalTrigger(hours=1),  # Executa a cada 1 hora
        id="placement_test_checker",
        replace_existing=True,
        max_instances=1  # Evita execuções simultâneas
    )
    print("✅ Job de verificação de testes de nivelamento agendado (a cada 1 hora)")
    
    yield
    # Parar o scheduler quando a aplicação desligar
    scheduler.shutdown()
    print("Scheduler shut down.")

app = FastAPI(
    title="Cal.com → Notion + WhatsApp Integration",
    description="Integration service that receives Cal.com webhooks and syncs with Notion and WhatsApp",
    version="1.0.4",
    lifespan=lifespan
)

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
        
        # ✅ NOVO: Envia contexto para a Zaia sobre o agendamento
        try:
            context_message = f"Reunião agendada para {attendee.name} em {formatted_pt}"
            ZaiaContextService().send_meeting_confirmation(whatsapp, context_message)
            print("✓ Contexto enviado para a Zaia com sucesso.")
        except Exception as e:
            print(f"⚠️ Erro ao enviar contexto para Zaia: {e}")

    # Notificações para admins, somente se tivermos uma página no Notion
    if page_id:
        schedule_messages(scheduler, attendee.name, start_dt, page_id, whatsapp)
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
        else:
            return {"success": False, "error": "Tipo de mensagem inválido. Use: 1d ou 4h."}
        
        when = {"1d": dt - timedelta(days=1), "4h": dt - timedelta(hours=4)}[req.which]

        if req.send_now:
            send_wa_message(phone, msg)
            
            # ✅ NOVO: Envia contexto para a Zaia
            try:
                ZaiaContextService().send_message_to_zaia(phone, msg, "test_message")
                print("✓ Contexto enviado para a Zaia.")
            except Exception as e:
                print(f"⚠️ Erro ao enviar contexto para Zaia: {e}")
            
            return {"success": True, "sent_now": True, "phone": phone, "message": msg}
        else:
            scheduler.add_job(send_wa_message, trigger=DateTrigger(run_date=when), args=[phone, msg], id=f"lead_whatsapp_{dt.timestamp()}_{req.which}", replace_existing=True)
            
            # ✅ REMOVIDO: Envio imediato para a Zaia sobre mensagem agendada
            # A mensagem só será enviada para a Zaia quando o scheduler executar
            
            return {"success": True, "scheduled_for": when.isoformat(), "phone": phone, "message": msg}
    except Exception as e:
        return {"success": False, "error": str(e)}

# -----------------------------------------------------------------------------
# Test endpoints
# -----------------------------------------------------------------------------
@app.get("/test/zaia-config")
async def test_zaia_config():
    """Testa a configuração da Zaia."""
    try:
        zaia_service = ZaiaContextService()
        return {
            "enabled": zaia_service.enabled,
            "agent_id": zaia_service.agent_id if zaia_service.enabled else None,
            "base_url": zaia_service.base_url if zaia_service.enabled else None,
            "api_key_configured": bool(zaia_service.api_key) if zaia_service.enabled else False
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/zaia-send")
async def test_zaia_send():
    """Testa o envio de uma mensagem para a Zaia."""
    try:
        zaia_service = ZaiaContextService()
        if not zaia_service.enabled:
            return {"error": "Zaia não está habilitada"}
        
        # Testa com um número fictício
        test_phone = "5511999999999"
        test_message = "Teste de integração com Zaia - " + datetime.now().strftime("%H:%M:%S")
        
        result = zaia_service.send_message_to_zaia(test_phone, test_message, "test")
        return {
            "success": result,
            "phone": test_phone,
            "message": test_message,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/schedule-messages")
async def test_schedule_messages():
    """Testa o agendamento de mensagens."""
    try:
        # Testa com uma data futura
        test_dt = datetime.now() + timedelta(minutes=2)
        test_name = "Teste"
        test_page_id = "test-page-id"
        test_whatsapp = "5511999999999"
        
        schedule_messages(scheduler, test_name, test_dt, test_page_id, test_whatsapp)
        return {
            "success": True,
            "scheduled_for": test_dt.isoformat(),
            "message": "Mensagens de teste agendadas para admins"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test/placement-tests")
async def test_placement_tests():
    """Testa a verificação de testes de nivelamento."""
    try:
        await placement_test_service.process_all_students()
        return {
            "success": True,
            "message": "Verificação de testes de nivelamento executada com sucesso",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)