from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings


class MongoState:
    client: AsyncIOMotorClient | None = None


mongo_state = MongoState()


async def connect_to_mongo() -> None:
    mongo_state.client = AsyncIOMotorClient(settings.mongodb_uri)


async def close_mongo_connection() -> None:
    if mongo_state.client is not None:
        mongo_state.client.close()
        mongo_state.client = None


def get_database() -> AsyncIOMotorDatabase:
    if mongo_state.client is None:
        raise RuntimeError("MongoDB client is not initialized")

    return mongo_state.client[settings.mongodb_database]
