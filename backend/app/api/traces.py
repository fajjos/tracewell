import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.schemas.trace import (
    SortOrder,
    TraceCreateResponse,
    TraceIngestRequest,
    TraceListResponse,
    TraceResponse,
    TraceSortField,
    TraceStatus,
)
from app.services.traces import (
    TraceAlreadyExistsError,
    TraceNotFoundError,
    TraceReadError,
    TraceStorageError,
    get_trace,
    ingest_trace,
    list_traces,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/traces", tags=["traces"])


@router.get("", response_model=TraceListResponse)
async def get_traces(
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    sort_by: TraceSortField = TraceSortField.CREATED_AT,
    sort_order: SortOrder = SortOrder.DESC,
    project_id: Annotated[Optional[str], Query(min_length=1, max_length=128)] = None,
    trace_status: Annotated[Optional[TraceStatus], Query(alias="status")] = None,
) -> TraceListResponse:
    try:
        result = await list_traces(
            database=database,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            project_id=project_id,
            trace_status=trace_status,
        )
    except TraceReadError as exc:
        logger.error("Trace list retrieval failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trace storage unavailable",
        ) from exc

    return TraceListResponse(
        items=[
            TraceResponse.model_validate(trace.model_dump(mode="python"))
            for trace in result.items
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.post(
    "",
    response_model=TraceCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_trace(
    trace_payload: TraceIngestRequest,
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TraceCreateResponse:
    try:
        result = await ingest_trace(trace_payload=trace_payload, database=database)
    except TraceAlreadyExistsError as exc:
        logger.warning(
            "Trace ingestion conflict",
            extra={"trace_id": exc.trace_id},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trace already exists",
        ) from exc
    except TraceStorageError as exc:
        logger.error(
            "Trace ingestion storage error",
            extra={"trace_id": exc.trace_id},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trace storage unavailable",
        ) from exc

    return TraceCreateResponse(trace_id=result.trace_id, issues=result.issues)


@router.get("/{trace_id}", response_model=TraceResponse)
async def get_trace_by_id(
    trace_id: Annotated[str, Path(min_length=1, max_length=128)],
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> TraceResponse:
    try:
        trace = await get_trace(trace_id=trace_id, database=database)
    except TraceNotFoundError as exc:
        logger.info(
            "Trace not found",
            extra={"trace_id": exc.trace_id},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found",
        ) from exc
    except TraceReadError as exc:
        logger.error(
            "Trace retrieval failed",
            extra={"trace_id": exc.trace_id},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trace storage unavailable",
        ) from exc

    return TraceResponse.model_validate(trace.model_dump(mode="python"))
