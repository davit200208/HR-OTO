from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class VerificationResult:
    verified: bool
    method: str
    reason: str = ""


class VerificationProvider(Protocol):
    async def verify(self, employee_id: str, captured_at: datetime, payload: dict) -> VerificationResult: ...


class PendingVerificationProvider:
    """No attendance method is activated until the product decision is made."""
    async def verify(self, employee_id: str, captured_at: datetime, payload: dict) -> VerificationResult:
        return VerificationResult(False, "pending", "Attendance verification method is not configured")
