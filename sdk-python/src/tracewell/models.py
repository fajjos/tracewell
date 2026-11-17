from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TraceStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class TraceToolCall(BaseModel):
    name: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(extra="allow")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Value must not be blank")

        return normalized_value


class TracePayload(BaseModel):
    trace_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    prompt: str = Field(min_length=1)
    response: str = ""
    provider: str = Field(default="unknown", min_length=1, max_length=64)
    model: str = Field(default="unknown", min_length=1, max_length=128)
    latency_ms: int = Field(ge=0)
    input_tokens: Optional[int] = Field(default=None, ge=0)
    output_tokens: Optional[int] = Field(default=None, ge=0)
    total_tokens: Optional[int] = Field(default=None, ge=0)
    cost: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    cost_is_estimated: Optional[bool] = None
    cost_source: Optional[str] = None
    usage_source: Optional[str] = None
    llm_calls: List[Dict[str, object]] = Field(default_factory=list)
    status: TraceStatus = TraceStatus.SUCCESS
    tool_calls: list[TraceToolCall] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "trace_id",
        "project_id",
        "session_id",
        "prompt",
        "provider",
        "model",
    )
    @classmethod
    def validate_non_blank_string(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Value must not be blank")

        return normalized_value

    @field_validator("created_at")
    @classmethod
    def validate_created_at_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        return value

    @model_validator(mode="after")
    def validate_total_tokens(self) -> "TracePayload":
        if self.input_tokens is None or self.output_tokens is None:
            return self
        expected_total = self.input_tokens + self.output_tokens
        if self.total_tokens is None:
            self.total_tokens = expected_total
            return self

        if self.total_tokens != expected_total:
            raise ValueError("total_tokens must equal input_tokens + output_tokens")

        return self


class TraceResult(BaseModel):
    trace_id: str
