from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel

from audit_log import audit_logger

@dataclass
class CalendarEvent:
    id: int
    user_id: str
    title: str
    start: datetime

class CalendarEventCreate(BaseModel):
    user_id: str
    title: str
    start: datetime

class CalendarEventOut(BaseModel):
    id: int
    user_id: str
    title: str
    start: datetime

class CalendarService:
    """Very small in-memory calendar integration prototype."""

    def __init__(self) -> None:
        self._events: Dict[int, CalendarEvent] = {}
        self._next_id: int = 1

    def create(self, data: CalendarEventCreate) -> CalendarEvent:
        ev = CalendarEvent(
            id=self._next_id,
            user_id=data.user_id,
            title=data.title,
            start=data.start,
        )
        self._events[ev.id] = ev
        self._next_id += 1
        audit_logger.log(actor=data.user_id, action="calendar_create", details=f"id={ev.id}")
        return ev

    def list_for_user(self, user_id: str) -> List[CalendarEvent]:
        return [e for e in self._events.values() if e.user_id == user_id]

calendar_service = CalendarService()
