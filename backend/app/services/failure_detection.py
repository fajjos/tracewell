from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FailureSignal:
    code: str
    message: str
    severity: str


def detect_failure_signals(trace_payload: dict[str, Any]) -> list[FailureSignal]:
    signals: list[FailureSignal] = []

    if trace_payload.get("error"):
        signals.append(
            FailureSignal(
                code="runtime_error",
                message="Trace payload contains an error field.",
                severity="error",
            )
        )

    latency_ms = trace_payload.get("latency_ms")
    if isinstance(latency_ms, int | float) and latency_ms > 30_000:
        signals.append(
            FailureSignal(
                code="high_latency",
                message="Trace latency exceeded 30 seconds.",
                severity="warning",
            )
        )

    return signals
