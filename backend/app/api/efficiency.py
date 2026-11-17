from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import settings
from app.database.mongodb import get_database
from app.models.trace import TraceDocument
from app.services.efficiency import analyze_trace, summarize_traces

router = APIRouter(prefix="/efficiency", tags=["efficiency"])


async def _load(database: AsyncIOMotorDatabase, project_id: str | None, days: int) -> list[TraceDocument]:
    query: dict[str, object] = {"created_at": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)}}
    if project_id:
        query["project_id"] = project_id
    try:
        docs = await database["traces"].find(query).sort("created_at", -1).limit(settings.efficiency_max_records).to_list(length=settings.efficiency_max_records)
        traces = []
        for doc in docs:
            try:
                traces.append(TraceDocument.from_mongo_document(doc))
            except Exception:
                continue
        return traces
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Trace storage unavailable") from exc


@router.get("/overview")
async def overview(database: Annotated[AsyncIOMotorDatabase, Depends(get_database)], project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None, days: Annotated[int, Query(ge=1, le=90)] = 30) -> dict[str, object]:
    return summarize_traces(await _load(database, project_id, days))


@router.get("/insights")
async def insights(database: Annotated[AsyncIOMotorDatabase, Depends(get_database)], project_id: Annotated[str | None, Query(min_length=1, max_length=128)] = None, days: Annotated[int, Query(ge=1, le=90)] = 30) -> dict[str, object]:
    summary = summarize_traces(await _load(database, project_id, days))
    return {"items": summary["insights"], "total": summary["detected_inefficiencies"]}


@router.get("/traces/{trace_id}")
async def trace_efficiency(trace_id: str, database: Annotated[AsyncIOMotorDatabase, Depends(get_database)]) -> dict[str, object]:
    doc = await database["traces"].find_one({"_id": trace_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    try:
        trace = TraceDocument.from_mongo_document(doc)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Trace data is malformed") from exc
    calls = [call.model_dump(mode="json") for call in trace.llm_calls]
    if not calls:
        calls = [{"model": trace.model, "provider": trace.provider, "input_tokens": trace.input_tokens, "output_tokens": trace.output_tokens, "total_tokens": trace.total_tokens, "latency_ms": trace.latency_ms, "cost": trace.cost, "cost_source": trace.cost_source, "usage_source": trace.usage_source}]
    return {"trace_id": trace.trace_id, "llm_calls": calls, "tool_calls": [call.model_dump(mode="json") for call in trace.tool_calls], "insights": analyze_trace(trace)}
