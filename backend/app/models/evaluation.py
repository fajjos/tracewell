from typing import Any

from pydantic import ConfigDict

from app.schemas.evaluation import EvaluationBase, EvaluationRunBase


class EvaluationDocument(EvaluationBase):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    def to_mongo_document(self) -> dict[str, Any]:
        document = self.model_dump(mode="python")
        document["_id"] = self.evaluation_id
        return document

    @classmethod
    def from_mongo_document(cls, document: dict[str, Any]) -> "EvaluationDocument":
        evaluation_data = document.copy()
        mongo_id = evaluation_data.pop("_id", None)
        if mongo_id is not None and str(mongo_id) != evaluation_data.get("evaluation_id"):
            raise ValueError("MongoDB _id must match evaluation_id")

        return cls.model_validate(evaluation_data)


class EvaluationRunDocument(EvaluationRunBase):
    model_config = ConfigDict(extra="forbid", use_enum_values=True)

    def to_mongo_document(self) -> dict[str, Any]:
        document = self.model_dump(mode="python")
        document["_id"] = self.run_id
        return document

    @classmethod
    def from_mongo_document(cls, document: dict[str, Any]) -> "EvaluationRunDocument":
        run_data = document.copy()
        mongo_id = run_data.pop("_id", None)
        if mongo_id is not None and str(mongo_id) != run_data.get("run_id"):
            raise ValueError("MongoDB _id must match run_id")

        return cls.model_validate(run_data)
