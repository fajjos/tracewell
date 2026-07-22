from pydantic import BaseModel


class ServiceStatusResponse(BaseModel):
    service: str
    version: str
    status: str


class HealthResponse(BaseModel):
    healthy: bool
