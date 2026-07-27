from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.failure_detection import FailureIssue


TRACE_EXAMPLE = {
    "trace_id": "trace_01JH8Y8X4NT7Q2B6Y5M9R3K2WA",
    "project_id": "project_01JH8Y6J9G2M4TQ0QF8D2H6V7P",
    "session_id": "session_01JH8Y78Z2NA5C4XQ8J9E1M3BK",
    "prompt": "Summarize the last customer support conversation.",
    "response": "The customer asked about their delayed shipment and requested an ETA.",
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "latency_ms": 842,
    "input_tokens": 32,
    "output_tokens": 18,
    "total_tokens": 50,
    "cost": 0.00014,
    "status": "success",
    "tool_calls": [],
    "created_at": "2026-07-22T15:30:00Z",
}


class TraceStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class TraceSortField(str, Enum):
    CREATED_AT = "created_at"
    LATENCY_MS = "latency_ms"
    TOTAL_TOKENS = "total_tokens"
    COST = "cost"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


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


class TraceBase(BaseModel):
    trace_id: str = Field(
        min_length=1,
        max_length=128,
        examples=[TRACE_EXAMPLE["trace_id"]],
    )
    project_id: str = Field(
        min_length=1,
        max_length=128,
        examples=[TRACE_EXAMPLE["project_id"]],
    )
    session_id: str = Field(
        min_length=1,
        max_length=128,
        examples=[TRACE_EXAMPLE["session_id"]],
    )
    prompt: str = Field(min_length=1, examples=[TRACE_EXAMPLE["prompt"]])
    response: str = Field(examples=[TRACE_EXAMPLE["response"]])
    provider: str = Field(
        min_length=1,
        max_length=64,
        examples=[TRACE_EXAMPLE["provider"]],
    )
    model: str = Field(min_length=1, max_length=128, examples=[TRACE_EXAMPLE["model"]])
    latency_ms: int = Field(ge=0, examples=[TRACE_EXAMPLE["latency_ms"]])
    input_tokens: int = Field(ge=0, examples=[TRACE_EXAMPLE["input_tokens"]])
    output_tokens: int = Field(ge=0, examples=[TRACE_EXAMPLE["output_tokens"]])
    total_tokens: int = Field(ge=0, examples=[TRACE_EXAMPLE["total_tokens"]])
    cost: float = Field(ge=0, allow_inf_nan=False, examples=[TRACE_EXAMPLE["cost"]])
    status: TraceStatus = Field(examples=[TRACE_EXAMPLE["status"]])
    tool_calls: list[TraceToolCall] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        examples=[TRACE_EXAMPLE["created_at"]],
    )

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [TRACE_EXAMPLE]},
    )

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
    def validate_total_tokens(self) -> "TraceBase":
        expected_total = self.input_tokens + self.output_tokens
        if self.total_tokens != expected_total:
            raise ValueError("total_tokens must equal input_tokens + output_tokens")

        return self


class TraceIngestRequest(TraceBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [TRACE_EXAMPLE]},
    )


class TraceCreateResponse(BaseModel):
    trace_id: str = Field(
        min_length=1,
        max_length=128,
        examples=[TRACE_EXAMPLE["trace_id"]],
    )
    issues: list[FailureIssue] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "trace_id": TRACE_EXAMPLE["trace_id"],
                    "issues": [],
                }
            ]
        },
    )


class TraceResponse(TraceBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [TRACE_EXAMPLE]},
    )


class TraceListResponse(BaseModel):
    items: list[TraceResponse]
    total: int = Field(ge=0, examples=[1])
    page: int = Field(ge=1, examples=[1])
    page_size: int = Field(ge=1, examples=[50])

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [TRACE_EXAMPLE],
                    "total": 1,
                    "page": 1,
                    "page_size": 50,
                }
            ]
        },
    )
