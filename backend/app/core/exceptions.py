import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled application exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "request_method": request.method,
            "request_path": request.url.path,
        },
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(Exception, unhandled_exception_handler)
