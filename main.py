
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import os
import requests
from dotenv import load_dotenv
# ----from dotenv import load_dotenv

load_dotenv()  # this reads .env and sets environment variables
# FastAPI app
# ---------------------------------------------------------

app = FastAPI(
    title="Elder Advice Agent",
    description="Provides gentle, general AI-powered advice for older adults and caregivers.",
)

AGENT_NAME = "elder-advice-agent"

# Groq API info
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # a common Groq Llama 3 chat model :contentReference[oaicite:4]{index=4}



# ---------------------------------------------------------
# Models from the project specification
# ---------------------------------------------------------

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: Role
    content: str


class AgentRequest(BaseModel):
    messages: List[Message]


class Status(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class AgentResponse(BaseModel):
    agent_name: str
    status: Status
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_last_user_message(request: AgentRequest) -> str:
    """Return the content of the most recent user message."""
    for msg in reversed(request.messages):
        if msg.role == Role.USER:
            return msg.content
    return ""


def call_online_llm(user_text: str) -> str:
    """
    Call Groq's online LLM API using a free-tier key.
    Requires GROQ_API_KEY to be set in environment (.env or env var).
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return (
            "I’m having trouble accessing my AI model right now because no API key is configured. "
            "Please set GROQ_API_KEY on the server. In the meantime, for health questions, "
            "it’s safest to speak to a doctor or nurse."
        )

    system_prompt = (
        "You are an elder advice assistant for older adults and their caregivers.\n"
        "You give gentle, respectful, simple advice about:\n"
        "- everyday aches and pains\n"
        "- comfort, sleep, daily routines, mood, loneliness, and safety\n"
        "- organising medication schedules (but not changing doses)\n\n"
        "SAFETY RULES (very important):\n"
        "- You are NOT a doctor and must NOT claim to be one.\n"
        "- Do NOT diagnose medical conditions.\n"
        "- Do NOT prescribe or change medicines or doses.\n"
        "- For strong, sudden, or worrying symptoms, always advise contacting a doctor "
        "or local emergency services.\n"
        "- Use short paragraphs and clear, simple language.\n"
        "- Be kind and supportive.\n"
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.4,
        "max_tokens": 512,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=8)

        # If Groq returns an error (400, 401, etc.), show the body so we know why
        if resp.status_code != 200:
            try:
                err = resp.json()
            except Exception:
                err = resp.text
            return (
                "I’m having trouble contacting my AI model right now (network or API issue). "
                "For anything related to health, especially if symptoms are new or strong, "
                "please contact a doctor or nurse.\n\n"
                f"(Groq error {resp.status_code}: {err})"
            )

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return (
            "I’m having trouble contacting my AI model right now (network or quota issue). "
            "For anything related to health, especially if symptoms are new or strong, "
            "please contact a doctor or nurse.\n\n"
            f"(Technical detail: {e})"
        )

def build_elder_advice_reply(user_text: str) -> str:
    """
    Core logic of the Elder Advice Agent:
    - Run basic safety checks.
    - If emergency-like, tell them to seek real help.
    - Otherwise, send the message to the online LLM.
    """

    if not user_text.strip():
        return (
            "Hello! I’m an elder advice companion powered by an online AI model. "
            "I can offer gentle, general guidance about common aches, daily routines, "
            "comfort, sleep, mood, and safety for older adults. "
            "I’m not a doctor and I can’t diagnose or prescribe medicines, "
            "so for medical concerns you should always talk to a healthcare professional."
        )

    lower = user_text.lower()

    # 1) Emergency / very serious signs -> do NOT ask the model, just escalate
    emergency_signs = [
        "chest pain",
        "trouble breathing",
        "difficulty breathing",
        "severe pain",
        "sudden weakness",
        "face drooping",
        "slurred speech",
        "can't move",
        "cannot move",
        "loss of consciousness",
        "fainted",
        "unresponsive",
    ]
    if any(sign in lower for sign in emergency_signs):
        return (
            "This may be an emergency. I’m not a medical professional and I can’t safely advise "
            "on this. Please call your local emergency number or seek urgent medical help immediately."
        )

    # 2) Otherwise, delegate to the online LLM
    return call_online_llm(user_text)


# ---------------------------------------------------------
# API endpoints
# ---------------------------------------------------------

@app.get("/")
def read_root():
    """Simple sanity-check endpoint."""
    return {"message": "Hello from Elder Advice Agent (online AI-powered)"}


@app.get("/api/elder-advice-agent/health")
def health_check():
    """
    Health check endpoint.
    Your supervisor system will call this to see if the agent is alive.
    """
    return {
        "status": "ok",
        "agent_name": AGENT_NAME,
        "ready": True,
    }


@app.post("/api/elder-advice-agent", response_model=AgentResponse)
def elder_advice_agent(request: AgentRequest):
    """
    Main agent endpoint.
    Expects an AgentRequest with a list of messages.
    Returns an AgentResponse containing a single 'message' field in data.
    """
    try:
        user_message = get_last_user_message(request)
        reply = build_elder_advice_reply(user_message)

        return AgentResponse(
            agent_name=AGENT_NAME,
            status=Status.SUCCESS,
            data={"message": reply},
            error_message=None,
        )
    except Exception as e:
        # Never crash; always return a well-formed error response
        return AgentResponse(
            agent_name=AGENT_NAME,
            status=Status.ERROR,
            data=None,
            error_message=str(e),
        )

# ---------------------------------------------------------
# Demo / prototype endpoints for WBS features
# ---------------------------------------------------------

from audit_log import audit_logger
from rule_engine import rule_engine_reply
from reminder_service import reminder_service, ReminderCreate, ReminderOut
from checkin_service import checkin_service, CheckInPrefsIn, CheckInStatusOut
from calendar_service import calendar_service, CalendarEventCreate, CalendarEventOut
from notifications_service import notifications_service, NotificationIn
from profiles_consent_service import (
    profiles_store,
    ProfileCreate,
    ConsentGrantIn,
    ProfileViewOut,
)


class ReminderActionIn(BaseModel):
    actor: str
    minutes: Optional[int] = None


# ---------- Rule engine demo ----------

@app.post("/demo/rule-engine", response_model=AgentResponse)
def demo_rule_engine(request: AgentRequest):
    user_text = get_last_user_message(request)
    rule_reply = rule_engine_reply(user_text)
    if rule_reply is None:
        message = (
            "No rule matched in the prototype rule engine. In the real system, "
            "this is where we fall back to the LLM-based core."
        )
    else:
        message = rule_reply

    return AgentResponse(
        agent_name=AGENT_NAME,
        status=Status.SUCCESS,
        data={"message": message},
        error_message=None,
    )


# ---------- Reminder service demo ----------

@app.post("/demo/reminders", response_model=ReminderOut)
def demo_create_reminder(data: ReminderCreate):
    rem = reminder_service.create(data)
    return ReminderOut(**rem.__dict__)


@app.get("/demo/reminders/{user_id}", response_model=List[ReminderOut])
def demo_list_reminders(user_id: str):
    rems = reminder_service.list_for_user(user_id)
    return [ReminderOut(**r.__dict__) for r in rems]


@app.post("/demo/reminders/{reminder_id}/confirm")
def demo_confirm_reminder(reminder_id: int, body: ReminderActionIn):
    reminder_service.confirm(reminder_id, actor=body.actor)
    return {"ok": True}


@app.post("/demo/reminders/{reminder_id}/snooze")
def demo_snooze_reminder(reminder_id: int, body: ReminderActionIn):
    minutes = body.minutes if body.minutes is not None else 10
    reminder_service.snooze(reminder_id, minutes=minutes, actor=body.actor)
    return {"ok": True}


# ---------- Check-in & escalation demo ----------

@app.post("/demo/checkin/prefs")
def demo_set_checkin_prefs(data: CheckInPrefsIn):
    checkin_service.set_prefs(data)
    return {"ok": True}


@app.post("/demo/checkin/{user_id}/prompt")
def demo_send_checkin_prompt(user_id: str):
    checkin_service.send_prompt(user_id)
    return {"ok": True}


@app.post("/demo/checkin/{user_id}/response")
def demo_record_checkin_response(user_id: str):
    checkin_service.record_response(user_id)
    return {"ok": True}


@app.get("/demo/checkin/{user_id}/status", response_model=CheckInStatusOut)
def demo_checkin_status(user_id: str):
    return checkin_service.evaluate_escalation(user_id)


# ---------- Calendar integration demo ----------

@app.post("/demo/calendar", response_model=CalendarEventOut)
def demo_create_calendar_event(data: CalendarEventCreate):
    ev = calendar_service.create(data)
    return CalendarEventOut(**ev.__dict__)


@app.get("/demo/calendar/{user_id}", response_model=List[CalendarEventOut])
def demo_list_calendar_events(user_id: str):
    events = calendar_service.list_for_user(user_id)
    return [CalendarEventOut(**e.__dict__) for e in events]


# ---------- Notifications demo ----------

@app.post("/demo/notify")
def demo_send_notification(data: NotificationIn):
    notifications_service.send(data)
    return {"ok": True, "sent_count": len(notifications_service.sent)}


# ---------- Profiles & consent demo ----------

@app.post("/demo/profiles")
def demo_create_profile(data: ProfileCreate):
    profiles_store.add_profile(data)
    return {"ok": True}


@app.post("/demo/consent")
def demo_grant_consent(data: ConsentGrantIn):
    profiles_store.grant_consent(data)
    return {"ok": True}


@app.get("/demo/profiles/{user_id}/view/{role}", response_model=ProfileViewOut)
def demo_view_profile(user_id: str, role: str):
    return profiles_store.view_profile(user_id=user_id, role=role)


# ---------- Caregiver dashboard + audit log (JSON only) ----------

@app.get("/demo/caregiver-dashboard")
def demo_caregiver_dashboard(caregiver_id: str = "caregiver-1"):
    elder_id = "elder-1"
    state = checkin_service.state.get(elder_id) if hasattr(checkin_service, "state") else None

    latest_checkin = {
        "last_prompt": state.last_prompt.isoformat() if state and state.last_prompt else None,
        "last_response": state.last_response.isoformat() if state and state.last_response else None,
        "escalation_needed": any(
            elder_id in esc for esc in getattr(checkin_service, "escalations", [])
        ),
    }

    dashboard = {
        "caregiver_id": caregiver_id,
        "elders": [
            {
                "user_id": elder_id,
                "latest_checkin": latest_checkin,
                "reminders": [r.__dict__ for r in reminder_service.list_for_user(elder_id)],
            }
        ],
        "escalations": getattr(checkin_service, "escalations", []),
    }
    return dashboard


@app.get("/demo/audit-log")
def demo_audit_log():
    return {"entries": audit_logger.list_entries()}