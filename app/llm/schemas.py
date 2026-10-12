from dataclasses import dataclass
from enum import Enum

class RequestStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class LLMResult:
    status: RequestStatus
    content: str | None = None
    error: str | None = None
    error_code: int | None = None

