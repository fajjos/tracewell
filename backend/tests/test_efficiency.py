from datetime import datetime, timedelta, timezone

import pytest

from app.models.trace import TraceDocument
from app.schemas.evaluation import AssertionType, EvaluationAssertion
from app.services.assertions import evaluate_assertion
from app.services.efficiency import analyze_trace, estimate_call_cost, summarize_traces


def make_trace(trace_id="trace-x", *, tokens=100, latency=500, prompt="hello", calls=None, tools=None, cost=0.001, created=None):
    return TraceDocument.model_validate({"trace_id": trace_id, "project_id": "p", "session_id": "s", "prompt": prompt, "response": "ok", "provider": "openai", "model": "gpt-4.1-mini", "latency_ms": latency, "input_tokens": tokens // 2, "output_tokens": tokens // 2, "total_tokens": tokens, "cost": cost, "status": "success", "tool_calls": tools or [], "llm_calls": calls or [], "created_at": created or datetime.now(timezone.utc)})


def test_token_aggregation_and_missing_metadata():
    result = summarize_traces([make_trace(tokens=20), make_trace("legacy", tokens=10)])
    assert result["total_tokens"] == 30
    legacy = TraceDocument.model_validate({"trace_id":"old", "project_id":"p", "session_id":"s", "prompt":"p", "response":"", "provider":"unknown", "model":"unknown", "latency_ms":1, "status":"success", "created_at":datetime.now(timezone.utc)})
    assert summarize_traces([legacy])["known_token_traces"] == 0


def test_cost_calculation_uses_configured_rates():
    assert estimate_call_cost("openai", "gpt-4.1-mini", 1_000_000, 1_000_000) == pytest.approx(2.0)
    assert estimate_call_cost("unknown", "other", 100, 100) is None


def test_repeated_calls_and_latency_detection():
    calls = [{"model":"m", "provider":"p", "prompt":"same", "latency_ms":6000}, {"model":"m", "provider":"p", "prompt":"same", "latency_ms":5}]
    found = {item["insight_type"] for item in analyze_trace(make_trace(calls=calls, latency=11_000))}
    assert "repeated_llm_calls" in found and "high_latency" in found


def test_excessive_tokens_and_long_prompt_detection():
    found = {item["insight_type"] for item in analyze_trace(make_trace(tokens=12_000, prompt="x" * 8_100))}
    assert {"excessive_tokens", "long_prompt"} <= found


def test_tool_repetition_and_token_spike():
    trace = make_trace(tools=[{"name":"search"}, {"name":"search"}])
    assert "repeated_tool_invocations" in {item["insight_type"] for item in analyze_trace(trace)}
    old = make_trace("old", tokens=5_000, created=datetime.now(timezone.utc)-timedelta(days=1))
    new = make_trace("new", tokens=8_500)
    spike = [item for item in summarize_traces([old, new])["insights"] if item["insight_type"] == "token_consumption_increase"]
    assert spike and spike[0]["evidence"]["increase_percent"] == 70


def test_efficiency_assertions_and_missing_usage_fail():
    trace = make_trace(tokens=100, calls=[{"model":"m", "input_tokens":50, "output_tokens":50, "total_tokens":100}])
    assertion = EvaluationAssertion(assertion_id="a", type=AssertionType.MAX_LLM_CALLS, name="calls", expected=0)
    assert not evaluate_assertion(assertion, trace).passed
    missing = TraceDocument.model_validate({"trace_id":"old", "project_id":"p", "session_id":"s", "prompt":"p", "response":"", "provider":"unknown", "model":"unknown", "latency_ms":1, "status":"success", "created_at":datetime.now(timezone.utc)})
    assertion = EvaluationAssertion(assertion_id="b", type=AssertionType.MAX_TOKENS, name="tokens", expected=100)
    result = evaluate_assertion(assertion, missing)
    assert result.passed is False and "missing" in result.message


def test_default_regression_assertions_include_efficiency_limits():
    from app.services.evaluations import build_default_assertions
    types = {item.type for item in build_default_assertions(make_trace(calls=[{"model":"gpt-4.1-mini", "provider":"openai", "input_tokens":50, "output_tokens":50, "total_tokens":100, "cost":0.001}]))}
    assert {AssertionType.MAX_INPUT_TOKENS, AssertionType.MAX_OUTPUT_TOKENS, AssertionType.MAX_ESTIMATED_COST, AssertionType.MAX_LLM_CALLS} <= types


@pytest.mark.asyncio
async def test_efficiency_api_responses(monkeypatch):
    from fastapi.testclient import TestClient
    from app.api.efficiency import _load
    from app.main import app
    from app.database.mongodb import get_database

    class Cursor:
        def sort(self, *args): return self
        def limit(self, *args): return self
        async def to_list(self, length): return [make_trace().to_mongo_document()]
    class Collection:
        documents = {}
        def find(self, query): return Cursor()
        async def find_one(self, query): return self.documents.get(query.get("_id")) or make_trace(query.get("_id", "trace-x")).to_mongo_document()
        async def insert_one(self, document):
            self.documents[str(document["_id"])] = document
            return type("InsertResult", (), {"inserted_id": document["_id"]})()
    class Database:
        collection = Collection()
        def __getitem__(self, key): return self.collection
    app.dependency_overrides[get_database] = lambda: Database()
    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/efficiency/overview").status_code == 200
            assert client.get("/api/v1/efficiency/insights").json()["total"] >= 0
            assert client.get("/api/v1/efficiency/traces/trace-x").status_code == 200
            legacy_payload = {"trace_id":"legacy-ingest", "project_id":"p", "session_id":"s", "prompt":"legacy prompt", "response":"ok", "provider":"openai", "model":"gpt-4.1-mini", "latency_ms":20, "status":"success", "created_at":datetime.now(timezone.utc).isoformat()}
            ingested = client.post("/api/v1/traces", json=legacy_payload)
            assert ingested.status_code == 201
            assert client.get("/api/v1/traces/legacy-ingest").json()["total_tokens"] is None
            evaluation = client.post("/api/v1/evaluations/from-trace/legacy-ingest")
            assert evaluation.status_code == 201
            run = client.post(f"/api/v1/evaluations/{evaluation.json()['evaluation_id']}/runs", json={"actual_trace_id":"trace-x"})
            assert run.status_code == 201
    finally:
        app.dependency_overrides.clear()
