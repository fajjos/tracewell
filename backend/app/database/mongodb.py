import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings


logger = logging.getLogger(__name__)


class MongoClientManager:
    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("MongoDB client is not initialized")

        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        return self.client[settings.mongodb_database]

    async def connect(self) -> None:
        if self._client is not None:
            return

        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
            tz_aware=True,
        )
        try:
            await client.admin.command("ping")
        except Exception:
            client.close()
            logger.exception("Failed to connect to MongoDB")
            raise

        self._client = client
        logger.info(
            "Connected to MongoDB",
            extra={"database": settings.mongodb_database},
        )

    async def close(self) -> None:
        if self._client is None:
            return

        self._client.close()
        self._client = None
        logger.info("Closed MongoDB connection")


mongo_client_manager = MongoClientManager()


async def connect_to_mongo() -> None:
    await mongo_client_manager.connect()


async def close_mongo_connection() -> None:
    await mongo_client_manager.close()


def get_mongo_client() -> AsyncIOMotorClient:
    return mongo_client_manager.client


def get_database() -> AsyncIOMotorDatabase:
    return mongo_client_manager.database
