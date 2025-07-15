from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from services.whatsapp_service import send_wa_bulk, send_wa_message

def schedule_messages(scheduler: AsyncIOScheduler, first_name: str, meeting_dt: datetime) -> None:
    meeting_str = meeting_dt.strftime("%H:%M")

    # 1 day before
    scheduler.add_job(
        send_wa_bulk,
        trigger=DateTrigger(run_date=meeting_dt - timedelta(days=1)),
        args=[f"Olá {first_name}, amanhã temos nossa reunião às {meeting_str}. Estamos ansiosos para falar com você!"],
        id=f"whatsapp_{meeting_dt.timestamp()}_1day",
        replace_existing=True,
    )

    # 4 hours before
    scheduler.add_job(
        send_wa_bulk,
        trigger=DateTrigger(run_date=meeting_dt - timedelta(hours=4)),
        args=[f"Oi {first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?"],
        id=f"whatsapp_{meeting_dt.timestamp()}_4h",
        replace_existing=True,
    )

    # 1 hour after
    scheduler.add_job(
        send_wa_bulk,
        trigger=DateTrigger(run_date=meeting_dt + timedelta(hours=1)),
        args=[f"{first_name}, obrigado pela reunião! Qualquer dúvida, estamos à disposição."],
        id=f"whatsapp_{meeting_dt.timestamp()}_after",
        replace_existing=True,
    )

def schedule_lead_messages(scheduler: AsyncIOScheduler, first_name: str, phone: str, dt: datetime):
    meeting_str = dt.strftime("%H:%M")
    scheduler.add_job(
        send_wa_message,
        trigger=DateTrigger(run_date=dt - timedelta(days=1)),
        args=[phone, f"Olá {first_name}, amanhã temos nossa reunião às {meeting_str}. Estamos ansiosos para falar com você!"],
        id=f"lead_whatsapp_{dt.timestamp()}_1day",
        replace_existing=True,
    )
    scheduler.add_job(
        send_wa_message,
        trigger=DateTrigger(run_date=dt - timedelta(hours=4)),
        args=[phone, f"Oi {first_name}, tudo certo para a nossa reunião hoje às {meeting_str}?"],
        id=f"lead_whatsapp_{dt.timestamp()}_4h",
        replace_existing=True,
    )
    scheduler.add_job(
        send_wa_message,
        trigger=DateTrigger(run_date=dt + timedelta(hours=1)),
        args=[phone, f"{first_name}, obrigado pela reunião! Qualquer dúvida, estamos à disposição."],
        id=f"lead_whatsapp_{dt.timestamp()}_after",
        replace_existing=True,
    ) 