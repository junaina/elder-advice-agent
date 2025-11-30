from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Set, Any

from pydantic import BaseModel

from audit_log import audit_logger

@dataclass
class Profile:
    user_id: str
    name: str
    age: int

@dataclass
class ConsentRecord:
    user_id: str
    viewer_role: str
    allowed_fields: Set[str]
    granted_at: datetime

class ProfileCreate(BaseModel):
    user_id: str
    name: str
    age: int

class ConsentGrantIn(BaseModel):
    user_id: str
    viewer_role: str
    allowed_fields: List[str]

class ProfileViewOut(BaseModel):
    fields: Dict[str, Any]

class ProfilesConsentStore:
    """In-memory profiles & consent store with least-privilege enforcement."""

    def __init__(self) -> None:
        self.profiles: Dict[str, Profile] = {}
        self.consents: List[ConsentRecord] = []

    def add_profile(self, data: ProfileCreate) -> None:
        self.profiles[data.user_id] = Profile(
            user_id=data.user_id, name=data.name, age=data.age
        )
        audit_logger.log(actor=data.user_id, action="profile_create")

    def grant_consent(self, data: ConsentGrantIn) -> None:
        self.consents.append(
            ConsentRecord(
                user_id=data.user_id,
                viewer_role=data.viewer_role,
                allowed_fields=set(data.allowed_fields),
                granted_at=datetime.utcnow(),
            )
        )
        audit_logger.log(actor=data.user_id, action="consent_grant", details=data.viewer_role)

    def _get_allowed_fields(self, user_id: str, role: str) -> Set[str]:
        fields: Set[str] = set()
        for c in self.consents:
            if c.user_id == user_id and c.viewer_role == role:
                fields |= c.allowed_fields
        return fields

    def view_profile(self, user_id: str, role: str) -> ProfileViewOut:
        profile = self.profiles[user_id]
        allowed = self._get_allowed_fields(user_id, role)
        result: Dict[str, Any] = {}
        for field_name in ["name", "age"]:
            if field_name in allowed:
                result[field_name] = getattr(profile, field_name)
        audit_logger.log(actor=role, action="profile_view", details=f"user_id={user_id}")
        return ProfileViewOut(fields=result)

profiles_store = ProfilesConsentStore()
