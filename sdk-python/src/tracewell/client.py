from dataclasses import dataclass, field
from datetime import datetime, timezone
from os import getenv
from typing import Dict, List, Optional, Union
from uuid import uuid4

import httpx

from tracewell.errors import TracewellAPIError, TracewellTransportError
from tracewell.models import TracePayload, TraceResult, TraceStatus


def _new_trace_id() -> str:
    return f"trace_{uuid4().hex}"


def _new_session_id() -> str:
    return f"session_{uuid4().hex}"


@dataclass
class Tracewell:
    api_key: Optional[str] = field(default_factory=lambda: getenv("TRACEWELL_API_KEY"))
    base_url: str = field(
        default_factory=lambda: getenv("TRACEWELL_BASE_URL", "http://localhost:8000")
    )
    project_id: str = field(
        default_factory=lambda: getenv("TRACEWELL_PROJECT_ID", "default")
    )
    session_id: str = field(default_factory=_new_session_id)
    timeout: float = 5.0

    def trace(
        self,
        *,
        prompt: str,
        response: str = "",
        latency_ms: int,
        provider: str = "unknown",
        model: str = "unknown",
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: Optional[int] = None,
        cost: float = 0.0,
        status: Union[TraceStatus, str] = TraceStatus.SUCCESS,
        tool_calls: Optional[List[Dict[str, object]]] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> TraceResult:
        payload = TracePayload(
            trace_id=trace_id or _new_trace_id(),
            project_id=project_id or self.project_id,
            session_id=session_id or self.session_id,
            prompt=prompt,
            response=response,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=(
                input_tokens + output_tokens if total_tokens is None else total_tokens
            ),
            cost=cost,
            status=status,
            tool_calls=tool_calls or [],
            created_at=created_at or datetime.now(timezone.utc),
        )

        return self._send_trace(payload)

    def _send_trace(self, payload: TracePayload) -> TraceResult:
        url = f"{self.base_url.rstrip('/')}/api/v1/traces"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Tracewell-API-Key"] = self.api_key

        try:
            response = httpx.post(
                url,
                json=payload.model_dump(mode="json"),
                headers=headers,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise TracewellTransportError(str(exc)) from exc

        if response.status_code >= 400:
            raise TracewellAPIError(
                status_code=response.status_code,
                message=response.text,
            )

        return TraceResult.model_validate(response.json())


TracewellClient = Tracewell


__all__ = ["Tracewell", "TracewellClient"]
