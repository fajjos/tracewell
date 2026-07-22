from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.database.mongodb import close_mongo_connection, connect_to_mongo


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting Tracewell API")
    await connect_to_mongo()
    yield
    await close_mongo_connection()
    logger.info("Stopped Tracewell API")


def create_app() -> FastAPI:
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router)

    return app


app = create_app()
