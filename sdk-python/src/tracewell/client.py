from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class TracewellClient:
    api_key: str | None = field(default_factory=lambda: getenv("TRACEWELL_API_KEY"))
    base_url: str = field(
        default_factory=lambda: getenv("TRACEWELL_BASE_URL", "http://localhost:8000")
    )

    def capture(self) -> None:
        raise NotImplementedError(
            "Trace capture will be implemented with the ingestion API."
        )
