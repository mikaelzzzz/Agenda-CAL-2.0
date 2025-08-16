# services/scheduling_service.py
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from services.whatsapp_service import send_wa_bulk, send_wa_message
from services.zaia_context_service import ZaiaContextService

# Inicializa o serviço de contexto da Zaia
zaia_context = ZaiaContextService()

def schedule_messages(scheduler: AsyncIOScheduler, first_name: str, meeting_dt: datetime, page_id: str, whatsapp: str | None) -> None:
    """Agenda lembretes para a equipe de vendas (admins) com links para Notion e WhatsApp."""
    meeting_str = meeting_dt.strftime("%H:%M")
    notion_page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
    
    # Monta a mensagem base - admins veem o nome completo
    base_message_8am = f"🔔 Lembrete de Reunião: Hoje temos um encontro com o lead *{first_name}* às *{meeting_str}*."
    base_message_1h = f"⏰ Atenção: A reunião com *{first_name}* começa em 1 hora, às *{meeting_str}*."
    
    # Adiciona os links
    links = f"\n\n📄 Notion: {notion_page_url}"
    if whatsapp:
        clean_phone = ''.join(filter(str.isdigit, whatsapp))
        links += f"\n💬 WhatsApp: wa.me/{clean_phone}"

    # Lembrete no dia da reunião, às 8h da manhã.
    meeting_day_8am = meeting_dt.replace(hour=8, minute=0, second=0, microsecond=0)
    
    if meeting_day_8am > datetime.now(tz=meeting_dt.tzinfo):
        scheduler.add_job(
            send_wa_bulk,
            trigger=DateTrigger(run_date=meeting_day_8am),
            args=[base_message_8am + links],
            id=f"admin_reminder_{meeting_dt.timestamp()}_8am",
            replace_existing=True,
        )

    # Lembrete 1 hora antes da reunião.
    one_hour_before = meeting_dt - timedelta(hours=1)
    if one_hour_before > datetime.now(tz=meeting_dt.tzinfo):
        scheduler.add_job(
            send_wa_bulk,
            trigger=DateTrigger(run_date=one_hour_before),
            args=[base_message_1h + links],
            id=f"admin_reminder_{meeting_dt.timestamp()}_1h",
            replace_existing=True,
        )

def schedule_lead_messages(scheduler: AsyncIOScheduler, first_name: str, phone: str, dt: datetime):
    """Agenda lembretes para o lead usando apenas o primeiro nome."""
    lead_first_name = first_name.split(' ')[0]
    meeting_str = dt.strftime("%H:%M")
    
    # Mensagem de 1 dia antes, agora com o vídeo.
    one_day_before_message = (
        f"Hello Hello, {lead_first_name}! Amanhã temos nossa reunião às {meeting_str}. Estamos ansiosos para falar com você!\n\n"
        "Aproveite e assista a este vídeo para entender por que nosso método é diferenciado!\n"
        "👉 https://www.youtube.com/watch?v=fKepCx3lMZI"
    )

    # Envia contexto para a Zaia sobre as mensagens agendadas
    try:
        zaia_context.send_reminder(phone, f"Lembrete agendado: {one_day_before_message}")
        zaia_context.send_reminder(phone, f"Lembrete agendado: Hello {lead_first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?")
        print(f"✓ Contexto de lembretes agendados enviado para a Zaia: {phone}")
    except Exception as e:
        print(f"⚠️ Erro ao enviar contexto de lembretes para Zaia: {e}")

    scheduler.add_job(
        send_wa_message,
        trigger=DateTrigger(run_date=dt - timedelta(days=1)),
        args=[phone, one_day_before_message, False, None, "reminder"],
        id=f"lead_whatsapp_{dt.timestamp()}_1day",
        replace_existing=True,
    )
    scheduler.add_job(
        send_wa_message,
        trigger=DateTrigger(run_date=dt - timedelta(hours=4)),
        args=[phone, f"Hello {lead_first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?", False, None, "reminder"],
        id=f"lead_whatsapp_{dt.timestamp()}_4h",
        replace_existing=True,
    )