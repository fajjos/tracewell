import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError

from app.database.evaluations import (
    count_evaluation_documents,
    count_evaluation_run_documents,
    find_evaluation_document,
    find_evaluation_run_document,
    insert_evaluation_document,
    insert_evaluation_run_document,
    list_evaluation_documents,
    list_evaluation_run_documents,
    replace_evaluation_document,
)
from app.models.evaluation import EvaluationDocument, EvaluationRunDocument
from app.models.trace import TraceDocument
from app.schemas.evaluation import (
    AssertionType,
    EvaluationAssertion,
    EvaluationRunStatus,
    EvaluationUpdateRequest,
)
from app.services.assertions import evaluate_assertions
from app.services.traces import TraceNotFoundError, get_trace


logger = logging.getLogger(__name__)

DEFAULT_LATENCY_MULTIPLIER = 2
MIN_DEFAULT_LATENCY_MS = 1_000


class EvaluationAlreadyExistsError(Exception):
    def __init__(self, evaluation_id: str) -> None:
        self.evaluation_id = evaluation_id
        super().__init__(f"Evaluation already exists: {evaluation_id}")


class EvaluationStorageError(Exception):
    def __init__(self, evaluation_id: Optional[str] = None) -> None:
        self.evaluation_id = evaluation_id
        super().__init__("Evaluation storage failed")


class EvaluationNotFoundError(Exception):
    def __init__(self, evaluation_id: str) -> None:
        self.evaluation_id = evaluation_id
        super().__init__(f"Evaluation not found: {evaluation_id}")


class EvaluationRunNotFoundError(Exception):
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Evaluation run not found: {run_id}")


class EvaluationReadError(Exception):
    pass


@dataclass(frozen=True)
class EvaluationListResult:
    items: list[EvaluationDocument]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True)
class EvaluationRunListResult:
    items: list[EvaluationRunDocument]
    total: int
    page: int
    page_size: int


def _new_evaluation_id() -> str:
    return f"eval_{uuid4().hex}"


def _new_assertion_id() -> str:
    return f"assert_{uuid4().hex}"


def _new_run_id() -> str:
    return f"run_{uuid4().hex}"


def build_default_assertions(source_trace: TraceDocument) -> list[EvaluationAssertion]:
    assertions = [
        EvaluationAssertion(
            assertion_id=_new_assertion_id(),
            type=AssertionType.RESPONSE_NON_EMPTY,
            name="Response is not empty",
        ),
        EvaluationAssertion(
            assertion_id=_new_assertion_id(),
            type=AssertionType.STATUS_EQUALS,
            name="Status matches source trace",
            expected=source_trace.status.value if hasattr(source_trace.status, "value") else source_trace.status,
        ),
        EvaluationAssertion(
            assertion_id=_new_assertion_id(),
            type=AssertionType.MAX_LATENCY_MS,
            name="Latency remains within threshold",
            expected=max(source_trace.latency_ms * DEFAULT_LATENCY_MULTIPLIER, MIN_DEFAULT_LATENCY_MS),
        ),
    ]

    if source_trace.total_tokens is not None and source_trace.total_tokens > 0:
        assertions.append(
            EvaluationAssertion(
                assertion_id=_new_assertion_id(),
                type=AssertionType.MAX_TOKENS,
                name="Token usage remains within threshold",
                expected=source_trace.total_tokens * DEFAULT_LATENCY_MULTIPLIER,
            )
        )

    for metric, value, assertion_type in (
        ("Input tokens", source_trace.input_tokens, AssertionType.MAX_INPUT_TOKENS),
        ("Output tokens", source_trace.output_tokens, AssertionType.MAX_OUTPUT_TOKENS),
    ):
        if value is not None and value > 0:
            assertions.append(EvaluationAssertion(assertion_id=_new_assertion_id(), type=assertion_type, name=f"{metric} remain within threshold", expected=value * DEFAULT_LATENCY_MULTIPLIER))
    if source_trace.cost is not None:
        assertions.append(EvaluationAssertion(assertion_id=_new_assertion_id(), type=AssertionType.MAX_ESTIMATED_COST, name="Cost remains within threshold", expected=source_trace.cost * DEFAULT_LATENCY_MULTIPLIER))
    if source_trace.llm_calls:
        assertions.append(EvaluationAssertion(assertion_id=_new_assertion_id(), type=AssertionType.MAX_LLM_CALLS, name="LLM calls remain within threshold", expected=len(source_trace.llm_calls) * DEFAULT_LATENCY_MULTIPLIER))

    for tool_call in source_trace.tool_calls:
        if not any(
            assertion.type == AssertionType.REQUIRED_TOOL_CALLED
            and assertion.expected == tool_call.name
            for assertion in assertions
        ):
            assertions.append(
                EvaluationAssertion(
                    assertion_id=_new_assertion_id(),
                    type=AssertionType.REQUIRED_TOOL_CALLED,
                    name=f"Required tool called: {tool_call.name}",
                    expected=tool_call.name,
                )
            )

    return assertions


async def create_evaluation_from_trace(
    trace_id: str,
    database: AsyncIOMotorDatabase,
) -> EvaluationDocument:
    source_trace = await get_trace(trace_id=trace_id, database=database)
    now = datetime.now(timezone.utc)
    evaluation = EvaluationDocument(
        evaluation_id=_new_evaluation_id(),
        project_id=source_trace.project_id,
        name=f"Regression test for {source_trace.trace_id}",
        description="Created from a captured Tracewell trace.",
        source_trace_id=source_trace.trace_id,
        assertions=build_default_assertions(source_trace),
        created_at=now,
        updated_at=now,
    )

    try:
        await insert_evaluation_document(database=database, evaluation=evaluation)
    except DuplicateKeyError as exc:
        raise EvaluationAlreadyExistsError(evaluation.evaluation_id) from exc
    except PyMongoError as exc:
        logger.exception("Evaluation insert failed", extra={"trace_id": trace_id})
        raise EvaluationStorageError(evaluation.evaluation_id) from exc

    return evaluation


async def get_evaluation(
    evaluation_id: str,
    database: AsyncIOMotorDatabase,
) -> EvaluationDocument:
    try:
        document = await find_evaluation_document(database=database, evaluation_id=evaluation_id)
    except PyMongoError as exc:
        raise EvaluationReadError() from exc

    if document is None:
        raise EvaluationNotFoundError(evaluation_id=evaluation_id)

    return EvaluationDocument.from_mongo_document(document)


async def update_evaluation(
    evaluation_id: str,
    payload: EvaluationUpdateRequest,
    database: AsyncIOMotorDatabase,
) -> EvaluationDocument:
    evaluation = await get_evaluation(evaluation_id=evaluation_id, database=database)
    update_data = payload.model_dump(exclude_unset=True)
    updated = EvaluationDocument.model_validate(
        {
            **evaluation.model_dump(mode="python"),
            **update_data,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    try:
        await replace_evaluation_document(database=database, evaluation=updated)
    except PyMongoError as exc:
        raise EvaluationStorageError(evaluation_id=evaluation_id) from exc

    return updated


async def list_evaluations(
    database: AsyncIOMotorDatabase,
    page: int,
    page_size: int,
    project_id: Optional[str],
) -> EvaluationListResult:
    query_filter: dict[str, object] = {}
    if project_id is not None:
        query_filter["project_id"] = project_id.strip()
    skip = (page - 1) * page_size

    try:
        total = await count_evaluation_documents(database=database, query_filter=query_filter)
        documents = await list_evaluation_documents(
            database=database,
            query_filter=query_filter,
            skip=skip,
            limit=page_size,
        )
    except PyMongoError as exc:
        raise EvaluationReadError() from exc

    return EvaluationListResult(
        items=[EvaluationDocument.from_mongo_document(document) for document in documents],
        total=total,
        page=page,
        page_size=page_size,
    )


async def run_evaluation(
    evaluation_id: str,
    actual_trace_id: str,
    database: AsyncIOMotorDatabase,
) -> EvaluationRunDocument:
    evaluation = await get_evaluation(evaluation_id=evaluation_id, database=database)
    try:
        actual_trace = await get_trace(trace_id=actual_trace_id, database=database)
    except TraceNotFoundError:
        raise

    assertion_results = evaluate_assertions(
        assertions=evaluation.assertions,
        actual_trace=actual_trace,
    )
    has_errors = any(
        not result.passed and result.severity == "error"
        for result in assertion_results
    )
    now = datetime.now(timezone.utc)
    run = EvaluationRunDocument(
        run_id=_new_run_id(),
        evaluation_id=evaluation.evaluation_id,
        project_id=evaluation.project_id,
        source_trace_id=evaluation.source_trace_id,
        actual_trace_id=actual_trace.trace_id,
        status=EvaluationRunStatus.FAILED if has_errors else EvaluationRunStatus.PASSED,
        assertion_results=assertion_results,
        started_at=now,
        completed_at=now,
    )

    try:
        await insert_evaluation_run_document(database=database, run=run)
    except PyMongoError as exc:
        raise EvaluationStorageError(evaluation_id=evaluation_id) from exc

    return run


async def get_evaluation_run(
    run_id: str,
    database: AsyncIOMotorDatabase,
) -> EvaluationRunDocument:
    try:
        document = await find_evaluation_run_document(database=database, run_id=run_id)
    except PyMongoError as exc:
        raise EvaluationReadError() from exc

    if document is None:
        raise EvaluationRunNotFoundError(run_id=run_id)

    return EvaluationRunDocument.from_mongo_document(document)


async def list_evaluation_runs(
    database: AsyncIOMotorDatabase,
    page: int,
    page_size: int,
    evaluation_id: Optional[str] = None,
) -> EvaluationRunListResult:
    query_filter: dict[str, object] = {}
    if evaluation_id is not None:
        query_filter["evaluation_id"] = evaluation_id
    skip = (page - 1) * page_size

    try:
        total = await count_evaluation_run_documents(database=database, query_filter=query_filter)
        documents = await list_evaluation_run_documents(
            database=database,
            query_filter=query_filter,
            skip=skip,
            limit=page_size,
        )
    except PyMongoError as exc:
        raise EvaluationReadError() from exc

    return EvaluationRunListResult(
        items=[EvaluationRunDocument.from_mongo_document(document) for document in documents],
        total=total,
        page=page,
        page_size=page_size,
    )
