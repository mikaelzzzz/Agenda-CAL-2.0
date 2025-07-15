from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class Attendee(BaseModel):
    name: str
    email: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    timeZone: Optional[str] = None


class UserFieldsResponses(BaseModel):
    Whatsapp: Optional[dict] = None


class Booking(BaseModel):
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    attendees: List[Attendee]
    uid: Optional[str] = None
    userFieldsResponses: Optional[UserFieldsResponses] = None
    eventDescription: Optional[str] = None
    videoCallData: Optional[dict] = None


class CalWebhookPayload(BaseModel):
    trigger_event: str = Field(..., alias="triggerEvent")
    payload: Booking


class ScheduleTestRequest(BaseModel):
    first_name: str
    meeting_datetime: str  # ISO format string


class ScheduleLeadTestRequest(BaseModel):
    email: str
    meeting_datetime: str  # ISO format string
    first_name: str = "Lead"


class SendLeadMessageRequest(BaseModel):
    email: str
    meeting_datetime: str  # ISO format string
    first_name: str = "Lead"
    which: str = "1d"  # opções: "1d", "4h", "after"
    send_now: bool = True 