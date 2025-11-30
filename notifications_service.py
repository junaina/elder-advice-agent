from __future__ import annotations
from dataclasses import dataclass
from typing import List

from pydantic import BaseModel

from audit_log import audit_logger

@dataclass
class NotificationRecord:
    channel: str
    to: str
    message: str

class NotificationIn(BaseModel):
    channel: str  # e.g. "email" or "sms"
    to: str
    message: str

class NotificationsService:
    """Prototype notifications layer – just logs to memory."""

    def __init__(self) -> None:
        self.sent: List[NotificationRecord] = []

    def send(self, data: NotificationIn) -> None:
        rec = NotificationRecord(channel=data.channel, to=data.to, message=data.message)
        self.sent.append(rec)
        audit_logger.log(actor=data.to, action="notification_send", details=f"channel={data.channel}")

notifications_service = NotificationsService()
