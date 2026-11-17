from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

import pytest
import pytest_asyncio
from pydantic import ValidationError

from app.models.evaluation import EvaluationDocument
from app.models.trace import TraceDocument
from app.schemas.evaluation import (
    AssertionType,
    EvaluationAssertion,
    EvaluationRunStatus,
    EvaluationUpdateRequest,
)
from app.services.evaluations import (
    EvaluationNotFoundError,
    build_default_assertions,
    create_evaluation_from_trace,
    get_evaluation,
    run_evaluation,
    update_evaluation,
)
from app.services.traces import TraceNotFoundError


class FakeInsertResult:
    def __init__(self, inserted_id: str) -> None:
        self.inserted_id = inserted_id


class FakeUpdateResult:
    matched_count = 1
    modified_count = 1


class FakeCursor:
    def __init__(self, documents: list[dict[str, object]]) -> None:
        self.documents = documents

    def sort(self, field: str, direction: int) -> "FakeCursor":
        reverse = direction < 0
        self.documents.sort(key=lambda document: document.get(field), reverse=reverse)
        return self

    def skip(self, count: int) -> "FakeCursor":
        self.documents = self.documents[count:]
        return self

    def limit(self, count: int) -> "FakeCursor":
        self.documents = self.documents[:count]
        return self

    async def to_list(self, length: int) -> list[dict[str, object]]:
        return deepcopy(self.documents[:length])


class FakeCollection:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, object]] = {}

    async def insert_one(self, document: dict[str, object]) -> FakeInsertResult:
        document_id = str(document["_id"])
        self.documents[document_id] = deepcopy(document)
        return FakeInsertResult(document_id)

    async def replace_one(
        self,
        query_filter: dict[str, object],
        document: dict[str, object],
    ) -> FakeUpdateResult:
        document_id = str(query_filter["_id"])
        self.documents[document_id] = deepcopy(document)
        return FakeUpdateResult()

    async def find_one(
        self,
        query_filter: dict[str, object],
    ) -> Optional[dict[str, object]]:
        document_id = query_filter.get("_id")
        if document_id is not None:
            document = self.documents.get(str(document_id))
            return deepcopy(document) if document is not None else None

        for document in self.documents.values():
            if all(document.get(key) == value for key, value in query_filter.items()):
                return deepcopy(document)

        return None

    async def count_documents(self, query_filter: dict[str, object]) -> int:
        return len(_filter_documents(self.documents.values(), query_filter))

    def find(self, query_filter: dict[str, object]) -> FakeCursor:
        return FakeCursor(_filter_documents(self.documents.values(), query_filter))


class FakeDatabase:
    def __init__(self) -> None:
        self.collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self.collections:
            self.collections[name] = FakeCollection()
        return self.collections[name]


def _filter_documents(
    documents: object,
    query_filter: dict[str, object],
) -> list[dict[str, object]]:
    return [
        deepcopy(document)
        for document in documents
        if all(document.get(key) == value for key, value in query_filter.items())
    ]


def make_trace(
    trace_id: str,
    *,
    response: str = "The customer needs billing email help.",
    status: str = "success",
    tool_calls: Optional[list[dict[str, object]]] = None,
    latency_ms: int = 400,
    total_tokens: int = 12,
) -> dict[str, object]:
    return {
        "_id": trace_id,
        "trace_id": trace_id,
        "project_id": "project-a",
        "session_id": "session-a",
        "prompt": "Help this customer.",
        "response": response,
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "latency_ms": latency_ms,
        "input_tokens": 5,
        "output_tokens": total_tokens - 5,
        "total_tokens": total_tokens,
        "cost": 0.001,
        "status": status,
        "tool_calls": tool_calls or [{"name": "billing_lookup"}],
        "created_at": datetime.now(timezone.utc),
    }


@pytest_asyncio.fixture
async def database() -> FakeDatabase:
    db = FakeDatabase()
    await db["traces"].insert_one(make_trace("trace_source"))
    await db["traces"].insert_one(make_trace("trace_actual"))
    return db


@pytest.mark.asyncio
async def test_create_evaluation_from_trace(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)

    assert evaluation.source_trace_id == "trace_source"
    assert evaluation.project_id == "project-a"
    assert any(
        assertion.type == AssertionType.RESPONSE_NON_EMPTY
        for assertion in evaluation.assertions
    )


@pytest.mark.asyncio
async def test_create_evaluation_from_missing_trace(database: FakeDatabase) -> None:
    with pytest.raises(TraceNotFoundError):
        await create_evaluation_from_trace("missing", database)


@pytest.mark.asyncio
async def test_passing_assertions(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)
    run = await run_evaluation(evaluation.evaluation_id, "trace_actual", database)

    assert run.status == EvaluationRunStatus.PASSED
    assert all(result.passed for result in run.assertion_results)


@pytest.mark.asyncio
async def test_failing_assertions(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)
    await database["traces"].insert_one(
        make_trace(
            "trace_bad",
            response="",
            status="error",
            tool_calls=[],
            latency_ms=5_000,
            total_tokens=100,
        )
    )

    run = await run_evaluation(evaluation.evaluation_id, "trace_bad", database)

    assert run.status == EvaluationRunStatus.FAILED
    assert any(not result.passed for result in run.assertion_results)


def test_unsupported_assertion_types_are_rejected() -> None:
    with pytest.raises(ValidationError):
        EvaluationAssertion(
            assertion_id="assert_bad",
            type="unknown_assertion",
            name="Unsupported assertion",
        )


@pytest.mark.asyncio
async def test_missing_evaluation(database: FakeDatabase) -> None:
    with pytest.raises(EvaluationNotFoundError):
        await run_evaluation("missing", "trace_actual", database)


@pytest.mark.asyncio
async def test_missing_actual_trace(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)

    with pytest.raises(TraceNotFoundError):
        await run_evaluation(evaluation.evaluation_id, "missing", database)


@pytest.mark.asyncio
async def test_evaluation_run_persistence(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)
    run = await run_evaluation(evaluation.evaluation_id, "trace_actual", database)

    stored = await database["evaluation_runs"].find_one({"_id": run.run_id})

    assert stored is not None
    assert stored["evaluation_id"] == evaluation.evaluation_id
    assert stored["actual_trace_id"] == "trace_actual"


@pytest.mark.asyncio
async def test_overall_pass_fail_ignores_warning_failures(database: FakeDatabase) -> None:
    evaluation = await create_evaluation_from_trace("trace_source", database)
    updated = await update_evaluation(
        evaluation.evaluation_id,
        payload=EvaluationUpdateRequest(
            assertions=[
                EvaluationAssertion(
                    assertion_id="assert_warning",
                    type=AssertionType.RESPONSE_CONTAINS,
                    name="Optional phrase",
                    expected="not present",
                    severity="warning",
                )
            ]
        ),
        database=database,
    )

    run = await run_evaluation(updated.evaluation_id, "trace_actual", database)

    assert run.status == EvaluationRunStatus.PASSED
    assert run.assertion_results[0].passed is False


def test_default_assertions_include_tool_status_latency_and_tokens() -> None:
    assertions = build_default_assertions(
        TraceDocument.from_mongo_document(make_trace("trace_source"))
    )

    assertion_types = {assertion.type for assertion in assertions}
    assert AssertionType.RESPONSE_NON_EMPTY in assertion_types
    assert AssertionType.STATUS_EQUALS in assertion_types
    assert AssertionType.REQUIRED_TOOL_CALLED in assertion_types
    assert AssertionType.MAX_LATENCY_MS in assertion_types
    assert AssertionType.MAX_TOKENS in assertion_types
