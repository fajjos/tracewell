from collections import Counter
from collections.abc import Sequence

from app.models.trace import TraceDocument
from app.schemas.evaluation import (
    AssertionResult,
    AssertionType,
    EvaluationAssertion,
)


class UnsupportedAssertionTypeError(Exception):
    def __init__(self, assertion_type: object) -> None:
        self.assertion_type = assertion_type
        super().__init__(f"Unsupported assertion type: {assertion_type}")


def evaluate_assertions(
    assertions: Sequence[EvaluationAssertion],
    actual_trace: TraceDocument,
) -> list[AssertionResult]:
    return [
        evaluate_assertion(assertion=assertion, actual_trace=actual_trace)
        for assertion in assertions
    ]


def evaluate_assertion(
    assertion: EvaluationAssertion,
    actual_trace: TraceDocument,
) -> AssertionResult:
    assertion_type = AssertionType(assertion.type)
    tool_names = [tool_call.name for tool_call in actual_trace.tool_calls]

    if assertion_type == AssertionType.RESPONSE_NON_EMPTY:
        actual = bool(actual_trace.response.strip())
        return _result(
            assertion=assertion,
            passed=actual,
            actual=actual_trace.response,
            message=(
                "Response was not empty."
                if actual
                else "Response was empty."
            ),
        )

    if assertion_type == AssertionType.RESPONSE_CONTAINS:
        expected = str(assertion.expected)
        passed = expected.lower() in actual_trace.response.lower()
        return _result(
            assertion=assertion,
            passed=passed,
            actual=actual_trace.response,
            message=(
                "Response contained the expected text."
                if passed
                else "Response did not contain the expected text."
            ),
        )

    if assertion_type == AssertionType.STATUS_EQUALS:
        actual = actual_trace.status.value if hasattr(actual_trace.status, "value") else actual_trace.status
        passed = actual == assertion.expected
        return _result(
            assertion=assertion,
            passed=passed,
            actual=actual,
            message=(
                "Trace status matched."
                if passed
                else "Trace status did not match."
            ),
        )

    if assertion_type == AssertionType.REQUIRED_TOOL_CALLED:
        expected = str(assertion.expected)
        passed = expected in tool_names
        return _result(
            assertion=assertion,
            passed=passed,
            actual=tool_names,
            message=(
                "Required tool was called."
                if passed
                else "Required tool was not called."
            ),
        )

    if assertion_type == AssertionType.FORBIDDEN_TOOL_NOT_CALLED:
        expected = str(assertion.expected)
        passed = expected not in tool_names
        return _result(
            assertion=assertion,
            passed=passed,
            actual=tool_names,
            message=(
                "Forbidden tool was not called."
                if passed
                else "Forbidden tool was called."
            ),
        )

    if assertion_type == AssertionType.MAX_TOOL_CALLS:
        expected = int(assertion.expected)
        counts = Counter(tool_names)
        max_count = max(counts.values(), default=0)
        passed = max_count <= expected
        return _result(
            assertion=assertion,
            passed=passed,
            actual=max_count,
            message=(
                "Tool call count stayed within the limit."
                if passed
                else "Tool call count exceeded the limit."
            ),
        )

    if assertion_type == AssertionType.MAX_LATENCY_MS:
        expected = int(assertion.expected)
        passed = actual_trace.latency_ms <= expected
        return _result(
            assertion=assertion,
            passed=passed,
            actual=actual_trace.latency_ms,
            message=(
                "Latency stayed within the limit."
                if passed
                else "Latency exceeded the limit."
            ),
        )

    if assertion_type == AssertionType.MAX_TOKENS:
        expected = int(assertion.expected)
        actual = actual_trace.total_tokens
        passed = actual is not None and actual <= expected
        return _result(
            assertion=assertion,
            passed=passed,
            actual=actual,
            message="Token usage metadata is missing." if actual is None else ("Token usage stayed within the limit." if passed else "Token usage exceeded the limit."),
        )

    call_input_tokens = [call.input_tokens for call in actual_trace.llm_calls]
    call_output_tokens = [call.output_tokens for call in actual_trace.llm_calls]
    aggregate_input = actual_trace.input_tokens if actual_trace.input_tokens is not None else (sum(value or 0 for value in call_input_tokens) if call_input_tokens and all(value is not None for value in call_input_tokens) else None)
    aggregate_output = actual_trace.output_tokens if actual_trace.output_tokens is not None else (sum(value or 0 for value in call_output_tokens) if call_output_tokens and all(value is not None for value in call_output_tokens) else None)
    call_costs = [call.cost for call in actual_trace.llm_calls]
    aggregate_cost = actual_trace.cost if actual_trace.cost is not None else (sum(value or 0 for value in call_costs) if call_costs and all(value is not None for value in call_costs) else None)
    efficiency_fields = {
        AssertionType.MAX_INPUT_TOKENS: aggregate_input,
        AssertionType.MAX_OUTPUT_TOKENS: aggregate_output,
        AssertionType.MAX_LLM_CALLS: len(actual_trace.llm_calls) if actual_trace.llm_calls else 1,
        AssertionType.MAX_ESTIMATED_COST: aggregate_cost,
    }
    if assertion_type in efficiency_fields:
        actual = efficiency_fields[assertion_type]
        expected = assertion.expected
        passed = actual is not None and actual <= expected
        metric = assertion_type.value.removeprefix("max_").replace("_", " ")
        return _result(assertion=assertion, passed=passed, actual=actual, message=f"{metric.capitalize()} metadata is missing." if actual is None else (f"{metric.capitalize()} stayed within the limit." if passed else f"{metric.capitalize()} exceeded the limit."))

    raise UnsupportedAssertionTypeError(assertion.type)


def _result(
    assertion: EvaluationAssertion,
    passed: bool,
    actual: object,
    message: str,
) -> AssertionResult:
    return AssertionResult(
        assertion_id=assertion.assertion_id,
        type=AssertionType(assertion.type),
        name=assertion.name,
        passed=passed,
        expected=assertion.expected,
        actual=actual,
        message=message,
        severity=assertion.severity,
    )
