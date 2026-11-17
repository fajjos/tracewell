from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Tracewell API", alias="TRACEWELL_APP_NAME")
    version: str = Field(default="0.1.0", alias="TRACEWELL_VERSION")
    environment: str = Field(default="development", alias="TRACEWELL_ENV")
    log_level: str = Field(default="INFO", alias="TRACEWELL_LOG_LEVEL")
    api_prefix: str = Field(default="/api/v1", alias="TRACEWELL_API_PREFIX")
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        alias="TRACEWELL_MONGODB_URI",
    )
    mongodb_database: str = Field(default="tracewell", alias="TRACEWELL_MONGODB_DATABASE")
    mongodb_server_selection_timeout_ms: int = Field(
        default=5_000,
        alias="TRACEWELL_MONGODB_SERVER_SELECTION_TIMEOUT_MS",
    )
    cors_origins_raw: str = Field(
        default="http://localhost:5173",
        alias="TRACEWELL_CORS_ORIGINS",
    )
    efficiency_max_records: int = Field(default=1000, ge=50, le=10000, alias="TRACEWELL_EFFICIENCY_MAX_RECORDS")
    model_pricing_raw: str = Field(default="openai/gpt-4.1-mini=0.40,1.60;openai/gpt-4.1=2.00,8.00", alias="TRACEWELL_MODEL_PRICING")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def model_pricing(self) -> dict[str, tuple[float, float]]:
        prices: dict[str, tuple[float, float]] = {}
        for entry in self.model_pricing_raw.split(";"):
            try:
                key, values = entry.strip().split("=", 1)
                input_price, output_price = values.split(",", 1)
                prices[key.strip().lower()] = (float(input_price), float(output_price))
            except (ValueError, TypeError):
                continue
        return prices


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
