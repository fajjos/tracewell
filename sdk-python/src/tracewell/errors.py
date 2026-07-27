class TracewellError(Exception):
    """Base exception for Tracewell SDK errors."""


class TracewellAPIError(TracewellError):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Tracewell API error {status_code}: {message}")


class TracewellTransportError(TracewellError):
    """Raised when the SDK cannot reach the Tracewell backend."""
