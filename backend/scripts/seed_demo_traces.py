from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PROJECT_ID = "demo-agent"


def utc_timestamp(minutes_ago: int) -> str:
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return timestamp.isoformat().replace("+00:00", "Z")


def build_demo_traces(project_id: str) -> list[dict[str, Any]]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    return [
        {
            "trace_id": f"demo_{run_id}_success",
            "project_id": project_id,
            "session_id": f"session_{run_id}_support",
            "prompt": "Summarize the latest customer support ticket.",
            "response": "The customer wants to update their billing email.",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "latency_ms": 420,
            "input_tokens": 42,
            "output_tokens": 28,
            "total_tokens": 70,
            "cost": 0.0003,
            "status": "success",
            "tool_calls": [],
            "created_at": utc_timestamp(4),
        },
        {
            "trace_id": f"demo_{run_id}_failed_response",
            "project_id": project_id,
            "session_id": f"session_{run_id}_billing",
            "prompt": "Look up invoice INV-2042 and explain the failed payment.",
            "response": "Payment lookup failed after the provider returned an error.",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "latency_ms": 1800,
            "input_tokens": 88,
            "output_tokens": 36,
            "total_tokens": 124,
            "cost": 0.0007,
            "status": "error",
            "tool_calls": [
                {
                    "name": "billing_lookup",
                    "latency_ms": 640,
                    "status": "error",
                }
            ],
            "created_at": utc_timestamp(3),
        },
        {
            "trace_id": f"demo_{run_id}_high_latency",
            "project_id": project_id,
            "session_id": f"session_{run_id}_research",
            "prompt": "Research five competitors and produce a pricing summary.",
            "response": "Completed, but the workflow took too long for an interactive request.",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "latency_ms": 65_000,
            "input_tokens": 980,
            "output_tokens": 740,
            "total_tokens": 1_720,
            "cost": 0.0094,
            "status": "success",
            "tool_calls": [
                {
                    "name": "web_search",
                    "latency_ms": 21_000,
                    "status": "success",
                },
                {
                    "name": "scrape_page",
                    "latency_ms": 18_000,
                    "status": "success",
                },
            ],
            "created_at": utc_timestamp(2),
        },
        {
            "trace_id": f"demo_{run_id}_high_tokens",
            "project_id": project_id,
            "session_id": f"session_{run_id}_legal",
            "prompt": "Review this long contract and extract every renewal clause.",
            "response": "Found renewal, cancellation, auto-renewal, and notice-period clauses.",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "latency_ms": 9_800,
            "input_tokens": 14_200,
            "output_tokens": 4_300,
            "total_tokens": 18_500,
            "cost": 0.072,
            "status": "success",
            "tool_calls": [],
            "created_at": utc_timestamp(1),
        },
        {
            "trace_id": f"demo_{run_id}_repeated_tool",
            "project_id": project_id,
            "session_id": f"session_{run_id}_docs",
            "prompt": "Find the refund policy in the internal help center.",
            "response": "Found the refund policy after repeated document searches.",
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "latency_ms": 5_400,
            "input_tokens": 620,
            "output_tokens": 180,
            "total_tokens": 800,
            "cost": 0.0031,
            "status": "success",
            "tool_calls": [
                {"name": "search_docs", "latency_ms": 900, "status": "success"},
                {"name": "search_docs", "latency_ms": 880, "status": "success"},
                {"name": "search_docs", "latency_ms": 930, "status": "success"},
                {"name": "search_docs", "latency_ms": 910, "status": "success"},
            ],
            "created_at": utc_timestamp(0),
        },
    ]


def post_trace(base_url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/traces"
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=timeout) as response:
        response_body = response.read().decode("utf-8")
        if not response_body:
            return {}

        return json.loads(response_body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed Tracewell with realistic demo traces through the public API."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Tracewell API base URL. Defaults to {DEFAULT_BASE_URL}.",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"Project ID to use for demo traces. Defaults to {DEFAULT_PROJECT_ID}.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds. Defaults to 10.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    traces = build_demo_traces(project_id=args.project_id)

    print(f"Seeding {len(traces)} demo traces into {args.base_url}")

    inserted = 0
    failed = 0
    for trace in traces:
        trace_id = trace["trace_id"]
        try:
            result = post_trace(
                base_url=args.base_url,
                payload=trace,
                timeout=args.timeout,
            )
        except HTTPError as exc:
            failed += 1
            detail = exc.read().decode("utf-8")
            print(f"FAILED {trace_id}: HTTP {exc.code} {detail}")
            continue
        except URLError as exc:
            print(f"Could not reach Tracewell at {args.base_url}: {exc.reason}")
            return 1
        except TimeoutError:
            print(f"Timed out connecting to Tracewell at {args.base_url}")
            return 1

        inserted += 1
        issue_count = len(result.get("issues", []))
        print(f"OK {trace_id}: {issue_count} issue(s)")

    print(f"Done. Inserted {inserted}, failed {failed}.")
    print("Open the dashboard and refresh: http://127.0.0.1:5173")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
