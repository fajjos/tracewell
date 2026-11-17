import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.schemas.evaluation import (
    EvaluationListResponse,
    EvaluationResponse,
    EvaluationRunCreateRequest,
    EvaluationRunListResponse,
    EvaluationRunResponse,
    EvaluationUpdateRequest,
)
from app.services.evaluations import (
    EvaluationNotFoundError,
    EvaluationReadError,
    EvaluationRunNotFoundError,
    EvaluationStorageError,
    create_evaluation_from_trace,
    get_evaluation,
    get_evaluation_run,
    list_evaluation_runs,
    list_evaluations,
    run_evaluation,
    update_evaluation,
)
from app.services.traces import TraceNotFoundError, TraceReadError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])
runs_router = APIRouter(prefix="/evaluation-runs", tags=["evaluations"])


@router.post(
    "/from-trace/{trace_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_from_trace_route(
    trace_id: Annotated[str, Path(min_length=1, max_length=128)],
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> EvaluationResponse:
    try:
        evaluation = await create_evaluation_from_trace(
            trace_id=trace_id,
            database=database,
        )
    except TraceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source trace not found",
        ) from exc
    except (TraceReadError, EvaluationStorageError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationResponse.model_validate(evaluation.model_dump(mode="python"))


@router.get("", response_model=EvaluationListResponse)
async def get_evaluations(
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    project_id: Annotated[Optional[str], Query(min_length=1, max_length=128)] = None,
) -> EvaluationListResponse:
    try:
        result = await list_evaluations(
            database=database,
            page=page,
            page_size=page_size,
            project_id=project_id,
        )
    except EvaluationReadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationListResponse(
        items=[
            EvaluationResponse.model_validate(item.model_dump(mode="python"))
            for item in result.items
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation_by_id(
    evaluation_id: Annotated[str, Path(min_length=1, max_length=128)],
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> EvaluationResponse:
    try:
        evaluation = await get_evaluation(evaluation_id=evaluation_id, database=database)
    except EvaluationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        ) from exc
    except EvaluationReadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationResponse.model_validate(evaluation.model_dump(mode="python"))


@router.patch("/{evaluation_id}", response_model=EvaluationResponse)
async def update_evaluation_by_id(
    evaluation_id: Annotated[str, Path(min_length=1, max_length=128)],
    payload: EvaluationUpdateRequest,
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> EvaluationResponse:
    try:
        evaluation = await update_evaluation(
            evaluation_id=evaluation_id,
            payload=payload,
            database=database,
        )
    except EvaluationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        ) from exc
    except EvaluationStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationResponse.model_validate(evaluation.model_dump(mode="python"))


@router.post(
    "/{evaluation_id}/runs",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_evaluation_by_id(
    evaluation_id: Annotated[str, Path(min_length=1, max_length=128)],
    payload: EvaluationRunCreateRequest,
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> EvaluationRunResponse:
    try:
        run = await run_evaluation(
            evaluation_id=evaluation_id,
            actual_trace_id=payload.actual_trace_id,
            database=database,
        )
    except EvaluationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        ) from exc
    except TraceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actual trace not found",
        ) from exc
    except (EvaluationReadError, TraceReadError, EvaluationStorageError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationRunResponse.model_validate(run.model_dump(mode="python"))


@router.get("/{evaluation_id}/runs", response_model=EvaluationRunListResponse)
async def get_runs_for_evaluation(
    evaluation_id: Annotated[str, Path(min_length=1, max_length=128)],
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> EvaluationRunListResponse:
    try:
        await get_evaluation(evaluation_id=evaluation_id, database=database)
        result = await list_evaluation_runs(
            database=database,
            page=page,
            page_size=page_size,
            evaluation_id=evaluation_id,
        )
    except EvaluationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found",
        ) from exc
    except EvaluationReadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationRunListResponse(
        items=[
            EvaluationRunResponse.model_validate(item.model_dump(mode="python"))
            for item in result.items
        ],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@runs_router.get("/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run_by_id(
    run_id: Annotated[str, Path(min_length=1, max_length=128)],
    database: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
) -> EvaluationRunResponse:
    try:
        run = await get_evaluation_run(run_id=run_id, database=database)
    except EvaluationRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation run not found",
        ) from exc
    except EvaluationReadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation storage unavailable",
        ) from exc

    return EvaluationRunResponse.model_validate(run.model_dump(mode="python"))
