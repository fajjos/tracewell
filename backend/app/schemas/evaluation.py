from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.trace import TraceStatus


class EvaluationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class EvaluationRunStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class AssertionType(str, Enum):
    RESPONSE_NON_EMPTY = "response_non_empty"
    RESPONSE_CONTAINS = "response_contains"
    STATUS_EQUALS = "status_equals"
    REQUIRED_TOOL_CALLED = "required_tool_called"
    FORBIDDEN_TOOL_NOT_CALLED = "forbidden_tool_not_called"
    MAX_TOOL_CALLS = "max_tool_calls"
    MAX_LATENCY_MS = "max_latency_ms"
    MAX_TOKENS = "max_tokens"
    MAX_INPUT_TOKENS = "max_input_tokens"
    MAX_OUTPUT_TOKENS = "max_output_tokens"
    MAX_LLM_CALLS = "max_llm_calls"
    MAX_ESTIMATED_COST = "max_estimated_cost"


class AssertionSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


class EvaluationAssertion(BaseModel):
    assertion_id: str = Field(min_length=1, max_length=128)
    type: AssertionType
    name: str = Field(min_length=1, max_length=160)
    expected: Any = None
    severity: AssertionSeverity = AssertionSeverity.ERROR

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("assertion_id", "name")
    @classmethod
    def validate_non_blank_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized

    @model_validator(mode="after")
    def validate_expected_value(self) -> "EvaluationAssertion":
        assertion_type = AssertionType(self.type)
        if assertion_type == AssertionType.RESPONSE_NON_EMPTY:
            if self.expected is not None:
                raise ValueError("response_non_empty does not accept an expected value")
        elif assertion_type == AssertionType.RESPONSE_CONTAINS:
            if not isinstance(self.expected, str) or not self.expected.strip():
                raise ValueError("response_contains expected value must be a non-empty string")
            self.expected = self.expected.strip()
        elif assertion_type == AssertionType.STATUS_EQUALS:
            if self.expected not in {status.value for status in TraceStatus}:
                raise ValueError("status_equals expected value must be success or error")
        elif assertion_type in {
            AssertionType.REQUIRED_TOOL_CALLED,
            AssertionType.FORBIDDEN_TOOL_NOT_CALLED,
        }:
            if not isinstance(self.expected, str) or not self.expected.strip():
                raise ValueError(f"{assertion_type.value} expected value must be a tool name")
            self.expected = self.expected.strip()
        elif assertion_type in {
            AssertionType.MAX_TOOL_CALLS,
            AssertionType.MAX_LATENCY_MS,
            AssertionType.MAX_TOKENS,
            AssertionType.MAX_INPUT_TOKENS,
            AssertionType.MAX_OUTPUT_TOKENS,
            AssertionType.MAX_LLM_CALLS,
        }:
            if not isinstance(self.expected, int) or self.expected < 0:
                raise ValueError(f"{assertion_type.value} expected value must be a non-negative integer")
        elif assertion_type == AssertionType.MAX_ESTIMATED_COST:
            if isinstance(self.expected, bool) or not isinstance(self.expected, (float, int)) or self.expected < 0:
                raise ValueError("max_estimated_cost expected value must be non-negative")

        return self


class EvaluationBase(BaseModel):
    evaluation_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    source_trace_id: str = Field(min_length=1, max_length=128)
    assertions: list[EvaluationAssertion] = Field(default_factory=list)
    status: EvaluationStatus = EvaluationStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    @field_validator("evaluation_id", "project_id", "name", "source_trace_id")
    @classmethod
    def validate_non_blank_string(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized

    @field_validator("created_at", "updated_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value


class EvaluationResponse(EvaluationBase):
    pass


class EvaluationListResponse(BaseModel):
    items: list[EvaluationResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class EvaluationUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    assertions: Optional[list[EvaluationAssertion]] = None

    model_config = ConfigDict(extra="forbid")


class EvaluationRunCreateRequest(BaseModel):
    actual_trace_id: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")

    @field_validator("actual_trace_id")
    @classmethod
    def validate_actual_trace_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value must not be blank")
        return normalized


class AssertionResult(BaseModel):
    assertion_id: str
    type: AssertionType
    name: str
    passed: bool
    expected: Any = None
    actual: Any = None
    message: str
    severity: AssertionSeverity = AssertionSeverity.ERROR

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class EvaluationRunBase(BaseModel):
    run_id: str = Field(min_length=1, max_length=128)
    evaluation_id: str = Field(min_length=1, max_length=128)
    project_id: str = Field(min_length=1, max_length=128)
    source_trace_id: str = Field(min_length=1, max_length=128)
    actual_trace_id: str = Field(min_length=1, max_length=128)
    status: EvaluationRunStatus
    assertion_results: list[AssertionResult]
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class EvaluationRunResponse(EvaluationRunBase):
    pass


class EvaluationRunListResponse(BaseModel):
    items: list[EvaluationRunResponse]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
