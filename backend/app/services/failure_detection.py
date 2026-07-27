from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from app.schemas.failure_detection import FailureIssue, FailureSeverity


class FailureRule(ABC):
    code: str

    @abstractmethod
    def evaluate(self, trace_payload: Mapping[str, Any]) -> Optional[FailureIssue]:
        raise NotImplementedError


class HighLatencyRule(FailureRule):
    code = "high_latency"

    def __init__(
        self,
        warning_threshold_ms: int = 30_000,
        error_threshold_ms: int = 60_000,
    ) -> None:
        self.warning_threshold_ms = warning_threshold_ms
        self.error_threshold_ms = error_threshold_ms

    def evaluate(self, trace_payload: Mapping[str, Any]) -> Optional[FailureIssue]:
        latency_ms = trace_payload.get("latency_ms")
        if not isinstance(latency_ms, (int, float)):
            return None

        if latency_ms >= self.error_threshold_ms:
            severity = FailureSeverity.ERROR
        elif latency_ms >= self.warning_threshold_ms:
            severity = FailureSeverity.WARNING
        else:
            return None

        return FailureIssue(
            code=self.code,
            message="Trace latency exceeded the configured threshold.",
            severity=severity,
            metadata={
                "latency_ms": latency_ms,
                "warning_threshold_ms": self.warning_threshold_ms,
                "error_threshold_ms": self.error_threshold_ms,
            },
        )


class HighTokenUsageRule(FailureRule):
    code = "high_token_usage"

    def __init__(
        self,
        warning_threshold_tokens: int = 8_000,
        error_threshold_tokens: int = 16_000,
    ) -> None:
        self.warning_threshold_tokens = warning_threshold_tokens
        self.error_threshold_tokens = error_threshold_tokens

    def evaluate(self, trace_payload: Mapping[str, Any]) -> Optional[FailureIssue]:
        total_tokens = trace_payload.get("total_tokens")
        if not isinstance(total_tokens, int):
            return None

        if total_tokens >= self.error_threshold_tokens:
            severity = FailureSeverity.ERROR
        elif total_tokens >= self.warning_threshold_tokens:
            severity = FailureSeverity.WARNING
        else:
            return None

        return FailureIssue(
            code=self.code,
            message="Trace token usage exceeded the configured threshold.",
            severity=severity,
            metadata={
                "total_tokens": total_tokens,
                "warning_threshold_tokens": self.warning_threshold_tokens,
                "error_threshold_tokens": self.error_threshold_tokens,
            },
        )


class FailedResponseRule(FailureRule):
    code = "failed_response"

    def evaluate(self, trace_payload: Mapping[str, Any]) -> Optional[FailureIssue]:
        status = trace_payload.get("status")
        response = trace_payload.get("response")
        error = trace_payload.get("error")

        if status == "error" or error:
            return FailureIssue(
                code=self.code,
                message="Trace completed with an error status.",
                severity=FailureSeverity.ERROR,
                metadata={"status": status, "has_error": bool(error)},
            )

        if isinstance(response, str) and not response.strip():
            return FailureIssue(
                code=self.code,
                message="Trace has an empty response.",
                severity=FailureSeverity.WARNING,
                metadata={"status": status},
            )

        return None


class RepeatedToolCallRule(FailureRule):
    code = "repeated_tool_call"

    def __init__(self, warning_threshold: int = 3, error_threshold: int = 5) -> None:
        self.warning_threshold = warning_threshold
        self.error_threshold = error_threshold

    def evaluate(self, trace_payload: Mapping[str, Any]) -> Optional[FailureIssue]:
        tool_names = self._extract_tool_names(trace_payload.get("tool_calls"))
        if not tool_names:
            return None

        tool_name, count = Counter(tool_names).most_common(1)[0]
        if count >= self.error_threshold:
            severity = FailureSeverity.ERROR
        elif count >= self.warning_threshold:
            severity = FailureSeverity.WARNING
        else:
            return None

        return FailureIssue(
            code=self.code,
            message="Trace contains repeated calls to the same tool.",
            severity=severity,
            metadata={
                "tool_name": tool_name,
                "call_count": count,
                "warning_threshold": self.warning_threshold,
                "error_threshold": self.error_threshold,
            },
        )

    def _extract_tool_names(self, tool_calls: Any) -> list[str]:
        if not isinstance(tool_calls, Sequence) or isinstance(tool_calls, str):
            return []

        names: list[str] = []
        for tool_call in tool_calls:
            name = self._extract_tool_name(tool_call)
            if name is not None:
                names.append(name)

        return names

    def _extract_tool_name(self, tool_call: Any) -> Optional[str]:
        if isinstance(tool_call, str):
            return tool_call.strip() or None

        if not isinstance(tool_call, Mapping):
            return None

        for key in ("name", "tool_name", "tool"):
            value = tool_call.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        function = tool_call.get("function")
        if isinstance(function, Mapping):
            value = function.get("name")
            if isinstance(value, str) and value.strip():
                return value.strip()

        return None


class FailureDetectionEngine:
    def __init__(self, rules: Optional[Sequence[FailureRule]] = None) -> None:
        self.rules = list(rules or DEFAULT_RULES)

    def detect(self, trace_payload: Mapping[str, Any]) -> list[FailureIssue]:
        issues: list[FailureIssue] = []
        for rule in self.rules:
            issue = rule.evaluate(trace_payload)
            if issue is not None:
                issues.append(issue)

        return issues


DEFAULT_RULES: tuple[FailureRule, ...] = (
    RepeatedToolCallRule(),
    HighLatencyRule(),
    HighTokenUsageRule(),
    FailedResponseRule(),
)


default_failure_detection_engine = FailureDetectionEngine()


def detect_failure_signals(trace_payload: Mapping[str, Any]) -> list[FailureIssue]:
    return default_failure_detection_engine.detect(trace_payload)


FailureSignal = FailureIssue
