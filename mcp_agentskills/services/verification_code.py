from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from mcp_agentskills.config.settings import settings


Purpose = Literal["login", "register", "bind_email"]


@dataclass
class CodeRecord:
    code: str
    expires_at: datetime
    resend_available_at: datetime
    max_attempts: int
    attempts_left: int


class VerificationCodeService:
    def __init__(
        self,
        code_length: int = 6,
        expires_in: int = 300,
        resend_interval: int = 60,
        max_attempts: int = 5,
    ):
        self._code_length = code_length
        self._expires_in = expires_in
        self._resend_interval = resend_interval
        self._max_attempts = max_attempts
        self._records: dict[tuple[str, Purpose], CodeRecord] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc).replace(microsecond=0)

    def _normalize(self, email: str) -> str:
        return email.strip().lower()

    def _generate_code(self) -> str:
        if settings.DEBUG:
            return "123456"
        upper = 10**self._code_length
        return str(secrets.randbelow(upper)).zfill(self._code_length)

    def send_code(self, email: str, purpose: Purpose) -> dict:
        key = (self._normalize(email), purpose)
        now = self._now()
        existing = self._records.get(key)
        if existing and now < existing.resend_available_at:
            raise ValueError("RESEND_TOO_FREQUENT")
        record = CodeRecord(
            code=self._generate_code(),
            expires_at=now + timedelta(seconds=self._expires_in),
            resend_available_at=now + timedelta(seconds=self._resend_interval),
            max_attempts=self._max_attempts,
            attempts_left=self._max_attempts,
        )
        self._records[key] = record
        return {
            "sent": True,
            "expires_in": self._expires_in,
            "resend_interval": self._resend_interval,
            "max_attempts": record.max_attempts,
            "attempts_left": record.attempts_left,
        }

    def verify_code(self, email: str, purpose: Purpose, code: str) -> None:
        key = (self._normalize(email), purpose)
        record = self._records.get(key)
        if not record:
            raise ValueError("CODE_INVALID")
        now = self._now()
        if now >= record.expires_at:
            self._records.pop(key, None)
            raise ValueError("CODE_EXPIRED")
        if record.attempts_left <= 0:
            raise ValueError("TOO_MANY_ATTEMPTS")
        if record.code != code:
            record.attempts_left -= 1
            raise ValueError("CODE_INVALID")
        self._records.pop(key, None)


_verification_service = VerificationCodeService()


def get_verification_service() -> VerificationCodeService:
    return _verification_service
