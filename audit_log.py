from datetime import datetime
from typing import List

class AuditLogger:
    """Simple in-memory audit logger for demo purposes."""

    def __init__(self) -> None:
        self._entries: List[str] = []

    def log(self, actor: str, action: str, details: str = "") -> None:
        timestamp = datetime.utcnow().isoformat()
        entry = f"{timestamp} actor={actor} action={action}"
        if details:
            entry += f" details={details}"
        self._entries.append(entry)

    def list_entries(self) -> List[str]:
        return list(self._entries)

audit_logger = AuditLogger()
