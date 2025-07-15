from datetime import datetime

def format_pt_br(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y as %H:%M") 