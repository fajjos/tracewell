from fastapi import APIRouter

from app.config import settings
from app.schemas.health import HealthResponse, ServiceStatusResponse


router = APIRouter(tags=["system"])


@router.get("/", response_model=ServiceStatusResponse)
async def service_status() -> ServiceStatusResponse:
    return ServiceStatusResponse(
        service=settings.app_name,
        version=settings.version,
        status="running",
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(healthy=True)
