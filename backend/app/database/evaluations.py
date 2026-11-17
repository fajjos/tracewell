from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING
from pymongo.results import InsertOneResult, UpdateResult

from app.models.evaluation import EvaluationDocument, EvaluationRunDocument


EVALUATIONS_COLLECTION = "evaluations"
EVALUATION_RUNS_COLLECTION = "evaluation_runs"


async def insert_evaluation_document(
    database: AsyncIOMotorDatabase,
    evaluation: EvaluationDocument,
) -> InsertOneResult:
    return await database[EVALUATIONS_COLLECTION].insert_one(
        evaluation.to_mongo_document()
    )


async def replace_evaluation_document(
    database: AsyncIOMotorDatabase,
    evaluation: EvaluationDocument,
) -> UpdateResult:
    return await database[EVALUATIONS_COLLECTION].replace_one(
        {"_id": evaluation.evaluation_id},
        evaluation.to_mongo_document(),
    )


async def find_evaluation_document(
    database: AsyncIOMotorDatabase,
    evaluation_id: str,
) -> Optional[dict[str, object]]:
    return await database[EVALUATIONS_COLLECTION].find_one({"_id": evaluation_id})


async def count_evaluation_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
) -> int:
    return await database[EVALUATIONS_COLLECTION].count_documents(query_filter)


async def list_evaluation_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
    skip: int,
    limit: int,
) -> list[dict[str, object]]:
    cursor = (
        database[EVALUATIONS_COLLECTION]
        .find(query_filter)
        .sort("created_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)


async def insert_evaluation_run_document(
    database: AsyncIOMotorDatabase,
    run: EvaluationRunDocument,
) -> InsertOneResult:
    return await database[EVALUATION_RUNS_COLLECTION].insert_one(
        run.to_mongo_document()
    )


async def find_evaluation_run_document(
    database: AsyncIOMotorDatabase,
    run_id: str,
) -> Optional[dict[str, object]]:
    return await database[EVALUATION_RUNS_COLLECTION].find_one({"_id": run_id})


async def count_evaluation_run_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
) -> int:
    return await database[EVALUATION_RUNS_COLLECTION].count_documents(query_filter)


async def list_evaluation_run_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
    skip: int,
    limit: int,
) -> list[dict[str, object]]:
    cursor = (
        database[EVALUATION_RUNS_COLLECTION]
        .find(query_filter)
        .sort("completed_at", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
