from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel

from audit_log import audit_logger

@dataclass
class Reminder:
    id: int
    user_id: str
    text: str
    when: datetime
    snoozed_until: Optional[datetime] = None
    confirmed: bool = False

class ReminderCreate(BaseModel):
    user_id: str
    text: str
    when: datetime

class ReminderOut(BaseModel):
    id: int
    user_id: str
    text: str
    when: datetime
    snoozed_until: Optional[datetime]
    confirmed: bool

class ReminderService:
    """In-memory reminder service with CRUD, snooze, confirm, and simple logs."""

    def __init__(self) -> None:
        self._reminders: Dict[int, Reminder] = {}
        self._next_id: int = 1

    def create(self, data: ReminderCreate) -> Reminder:
        rem = Reminder(
            id=self._next_id,
            user_id=data.user_id,
            text=data.text,
            when=data.when,
        )
        self._reminders[rem.id] = rem
        self._next_id += 1
        audit_logger.log(actor=data.user_id, action="reminder_create", details=f"id={rem.id}")
        return rem

    def list_for_user(self, user_id: str) -> List[Reminder]:
        return [r for r in self._reminders.values() if r.user_id == user_id]

    def delete(self, reminder_id: int, actor: str) -> None:
        if reminder_id in self._reminders:
            del self._reminders[reminder_id]
            audit_logger.log(actor=actor, action="reminder_delete", details=f"id={reminder_id}")

    def confirm(self, reminder_id: int, actor: str) -> None:
        if reminder_id in self._reminders:
            self._reminders[reminder_id].confirmed = True
            audit_logger.log(actor=actor, action="reminder_confirm", details=f"id={reminder_id}")

    def snooze(self, reminder_id: int, minutes: int, actor: str) -> None:
        if reminder_id in self._reminders:
            r = self._reminders[reminder_id]
            r.snoozed_until = datetime.utcnow() + timedelta(minutes=minutes)
            audit_logger.log(
                actor=actor,
                action="reminder_snooze",
                details=f"id={reminder_id} minutes={minutes}",
            )

    def due_at(self, now: datetime) -> List[Reminder]:
        due: List[Reminder] = []
        for r in self._reminders.values():
            target = r.snoozed_until or r.when
            if not r.confirmed and target <= now:
                due.append(r)
        return due

reminder_service = ReminderService()
