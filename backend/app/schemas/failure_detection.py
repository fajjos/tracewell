from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FailureSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class FailureIssue(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1)
    severity: FailureSeverity
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")
