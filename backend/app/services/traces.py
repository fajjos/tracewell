import logging
from dataclasses import dataclass
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database.traces import (
    count_trace_documents,
    find_trace_document,
    insert_trace_document,
    list_trace_documents,
)
from app.models.trace import TraceDocument
from app.schemas.failure_detection import FailureIssue
from app.schemas.trace import SortOrder, TraceBase, TraceSortField, TraceStatus
from app.services.failure_detection import detect_failure_signals


logger = logging.getLogger(__name__)


class TraceAlreadyExistsError(Exception):
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        super().__init__(f"Trace already exists: {trace_id}")


class TraceStorageError(Exception):
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        super().__init__(f"Trace storage failed: {trace_id}")


class TraceNotFoundError(Exception):
    def __init__(self, trace_id: str) -> None:
        self.trace_id = trace_id
        super().__init__(f"Trace not found: {trace_id}")


class TraceReadError(Exception):
    def __init__(self, trace_id: Optional[str] = None) -> None:
        self.trace_id = trace_id
        super().__init__("Trace read failed")


@dataclass(frozen=True)
class TraceListResult:
    items: list[TraceDocument]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class TraceIngestResult:
    trace_id: str
    issues: list[FailureIssue]


async def ingest_trace(
    trace_payload: TraceBase,
    database: AsyncIOMotorDatabase,
) -> TraceIngestResult:
    trace = TraceDocument.model_validate(trace_payload.model_dump(mode="python"))
    issues = detect_failure_signals(trace.model_dump(mode="python"))

    try:
        result = await insert_trace_document(database=database, trace=trace)
    except DuplicateKeyError as exc:
        logger.warning(
            "Trace insert rejected because trace_id already exists",
            extra={"trace_id": trace.trace_id},
        )
        raise TraceAlreadyExistsError(trace_id=trace.trace_id) from exc
    except PyMongoError as exc:
        logger.exception(
            "Trace insert failed",
            extra={"trace_id": trace.trace_id},
        )
        raise TraceStorageError(trace_id=trace.trace_id) from exc

    inserted_id = str(result.inserted_id)
    logger.info(
        "Trace ingested",
        extra={
            "trace_id": trace.trace_id,
            "project_id": trace.project_id,
            "status": trace.status,
            "detected_issue_count": len(issues),
        },
    )

    return TraceIngestResult(trace_id=inserted_id, issues=issues)


async def get_trace(
    trace_id: str,
    database: AsyncIOMotorDatabase,
) -> TraceDocument:
    try:
        document = await find_trace_document(database=database, trace_id=trace_id)
    except PyMongoError as exc:
        logger.exception(
            "Trace lookup failed",
            extra={"trace_id": trace_id},
        )
        raise TraceReadError(trace_id=trace_id) from exc

    if document is None:
        raise TraceNotFoundError(trace_id=trace_id)

    return TraceDocument.from_mongo_document(document)


async def list_traces(
    database: AsyncIOMotorDatabase,
    page: int,
    page_size: int,
    sort_by: TraceSortField,
    sort_order: SortOrder,
    project_id: Optional[str],
    trace_status: Optional[TraceStatus],
) -> TraceListResult:
    query_filter: dict[str, object] = {}
    if project_id is not None:
        query_filter["project_id"] = project_id.strip()
    if trace_status is not None:
        query_filter["status"] = trace_status.value

    sort_direction = ASCENDING if sort_order == SortOrder.ASC else DESCENDING
    skip = (page - 1) * page_size

    try:
        total = await count_trace_documents(
            database=database,
            query_filter=query_filter,
        )
        documents = await list_trace_documents(
            database=database,
            query_filter=query_filter,
            sort_field=sort_by.value,
            sort_direction=sort_direction,
            skip=skip,
            limit=page_size,
        )
    except PyMongoError as exc:
        logger.exception(
            "Trace list query failed",
            extra={
                "project_id": project_id,
                "status": trace_status,
                "page": page,
                "page_size": page_size,
                "sort_by": sort_by,
                "sort_order": sort_order,
            },
        )
        raise TraceReadError() from exc

    return TraceListResult(
        items=[TraceDocument.from_mongo_document(document) for document in documents],
        total=total,
        page=page,
        page_size=page_size,
    )
