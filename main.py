# main.py

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
