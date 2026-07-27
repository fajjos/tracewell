from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import InsertOneResult
from typing import Optional

from app.models.trace import TraceDocument


TRACES_COLLECTION = "traces"


async def insert_trace_document(
    database: AsyncIOMotorDatabase,
    trace: TraceDocument,
) -> InsertOneResult:
    return await database[TRACES_COLLECTION].insert_one(trace.to_mongo_document())


async def find_trace_document(
    database: AsyncIOMotorDatabase,
    trace_id: str,
) -> Optional[dict[str, object]]:
    return await database[TRACES_COLLECTION].find_one({"_id": trace_id})


async def count_trace_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
) -> int:
    return await database[TRACES_COLLECTION].count_documents(query_filter)


async def list_trace_documents(
    database: AsyncIOMotorDatabase,
    query_filter: dict[str, object],
    sort_field: str,
    sort_direction: int,
    skip: int,
    limit: int,
) -> list[dict[str, object]]:
    cursor = (
        database[TRACES_COLLECTION]
        .find(query_filter)
        .sort(sort_field, sort_direction)
        .skip(skip)
        .limit(limit)
    )
    return await cursor.to_list(length=limit)
