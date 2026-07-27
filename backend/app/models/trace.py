from typing import Any

from pydantic import ConfigDict

from app.schemas.trace import TRACE_EXAMPLE, TraceBase, TraceStatus


class TraceDocument(TraceBase):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [TRACE_EXAMPLE]},
        use_enum_values=True,
    )

    def to_mongo_document(self) -> dict[str, Any]:
        document = self.model_dump(mode="python")
        document["_id"] = self.trace_id
        return document

    @classmethod
    def from_mongo_document(cls, document: dict[str, Any]) -> "TraceDocument":
        trace_data = document.copy()
        mongo_id = trace_data.pop("_id", None)
        if mongo_id is not None and str(mongo_id) != trace_data.get("trace_id"):
            raise ValueError("MongoDB _id must match trace_id")

        return cls.model_validate(trace_data)


__all__ = ["TraceDocument", "TraceStatus"]
