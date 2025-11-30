from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel

from audit_log import audit_logger

@dataclass
class CaregiverPrefs:
    user_id: str
    caregiver_contact: str
    escalate_after_minutes: int

@dataclass
class CheckInState:
    user_id: str
    last_prompt: Optional[datetime] = None
    last_response: Optional[datetime] = None

class CheckInPrefsIn(BaseModel):
    user_id: str
    caregiver_contact: str
    escalate_after_minutes: int

class CheckInStatusOut(BaseModel):
    user_id: str
    last_prompt: Optional[datetime]
    last_response: Optional[datetime]
    escalation_needed: bool

class CheckInService:
    """Prototype daily check-in and escalation logic."""

    def __init__(self) -> None:
        self.prefs: Dict[str, CaregiverPrefs] = {}
        self.state: Dict[str, CheckInState] = {}
        self.escalations: List[str] = []

    def set_prefs(self, data: CheckInPrefsIn) -> None:
        self.prefs[data.user_id] = CaregiverPrefs(
            user_id=data.user_id,
            caregiver_contact=data.caregiver_contact,
            escalate_after_minutes=data.escalate_after_minutes,
        )
        self.state.setdefault(data.user_id, CheckInState(user_id=data.user_id))
        audit_logger.log(actor=data.user_id, action="checkin_set_prefs")

    def send_prompt(self, user_id: str, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        st = self.state.setdefault(user_id, CheckInState(user_id=user_id))
        st.last_prompt = now
        audit_logger.log(actor=user_id, action="checkin_prompt_sent")

    def record_response(self, user_id: str, now: Optional[datetime] = None) -> None:
        now = now or datetime.utcnow()
        st = self.state.setdefault(user_id, CheckInState(user_id=user_id))
        st.last_response = now
        audit_logger.log(actor=user_id, action="checkin_response_received")

    def evaluate_escalation(self, user_id: str, now: Optional[datetime] = None) -> CheckInStatusOut:
        now = now or datetime.utcnow()
        st = self.state.setdefault(user_id, CheckInState(user_id=user_id))
        prefs = self.prefs.get(user_id)
        escalate = False
        if prefs and st.last_prompt and (not st.last_response or st.last_response < st.last_prompt):
            if now - st.last_prompt >= timedelta(minutes=prefs.escalate_after_minutes):
                escalate = True
                msg = f"Escalate for {user_id} to {prefs.caregiver_contact} at {now.isoformat()}"
                self.escalations.append(msg)
                audit_logger.log(actor=user_id, action="checkin_escalation", details=msg)
        return CheckInStatusOut(
            user_id=user_id,
            last_prompt=st.last_prompt,
            last_response=st.last_response,
            escalation_needed=escalate,
        )

checkin_service = CheckInService()
