from collections import Counter, defaultdict
from hashlib import sha256
from typing import Any

from app.config import settings
from app.models.trace import TraceDocument


def estimate_call_cost(provider: str, model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    """Estimate USD using configured USD per million input/output tokens."""
    if input_tokens is None or output_tokens is None:
        return None
    rates = settings.model_pricing.get(f"{provider}/{model}".lower())
    if rates is None:
        return None
    return (input_tokens * rates[0] + output_tokens * rates[1]) / 1_000_000


def analyze_trace(trace: TraceDocument) -> list[dict[str, Any]]:
    calls = trace.llm_calls
    insights: list[dict[str, Any]] = []
    prompts = [call.prompt.strip().lower() for call in calls if call.prompt]
    prompt_counts = Counter(sha256(prompt.encode()).hexdigest() for prompt in prompts)
    repeated = [digest for digest, count in prompt_counts.items() if count > 1]
    if repeated:
        insights.append(_insight(trace, "repeated_llm_calls", "medium", "The same prompt was recorded for multiple model calls.", {"llm_calls": len(calls), "repeated_prompt_groups": len(repeated)}, "Repeated requests may add cost and latency.", "Investigate caching or consolidating repeated requests.", "Matching prompts do not prove that calls are redundant."))
    if len(calls) > 1 and not prompts:
        insights.append(_insight(trace, "multiple_llm_calls", "low", "Multiple model calls were recorded without prompt data for similarity analysis.", {"llm_calls": len(calls)}, "Review whether calls can share work or context.", "Inspect call purposes and consider caching or consolidation.", "Prompt data was not captured, so similarity cannot be assessed."))
    if trace.total_tokens is not None and trace.total_tokens >= 10_000:
        insights.append(_insight(trace, "excessive_tokens", "high", "Execution consumed at least 10,000 tokens.", {"total_tokens": trace.total_tokens}, "High token volume can increase cost and latency.", "Review prompt context and output length."))
    if len(trace.prompt) >= 8_000:
        insights.append(_insight(trace, "long_prompt", "medium", "The recorded prompt is unusually long.", {"prompt_characters": len(trace.prompt)}, "Long prompts may consume additional input tokens.", "Remove context that is not needed for this operation."))
    slow_calls = [{"model": call.model, "latency_ms": call.latency_ms} for call in calls if call.latency_ms is not None and call.latency_ms >= 5_000]
    if trace.latency_ms >= 10_000 or slow_calls:
        insights.append(_insight(trace, "high_latency", "high", "Execution or an individual model call had high latency.", {"execution_latency_ms": trace.latency_ms, "slow_calls": slow_calls}, "Long latency can slow agent workflows.", "Inspect call-level timing and compare faster alternatives."))
    tool_counts = Counter(call.name for call in trace.tool_calls)
    repeated_tools = {name: count for name, count in tool_counts.items() if count > 1}
    if repeated_tools:
        insights.append(_insight(trace, "repeated_tool_invocations", "medium", "One or more tools were invoked repeatedly.", {"tools": repeated_tools}, "Repeated tool work may increase execution time.", "Investigate whether tool results can be reused."))
    cost = trace.cost
    if cost is None and calls:
        call_costs = [call.cost if call.cost is not None else estimate_call_cost(call.provider, call.model, call.input_tokens, call.output_tokens) for call in calls]
        cost = sum(value for value in call_costs if value is not None) if call_costs and all(value is not None for value in call_costs) else None
    if cost is not None and cost >= 0.05 and trace.total_tokens is not None and trace.total_tokens < 1_000:
        insights.append(_insight(trace, "expensive_model_for_small_operation", "low", "A comparatively costly execution used fewer than 1,000 tokens.", {"cost": cost, "total_tokens": trace.total_tokens, "model": trace.model}, "A lower cost model may reduce spend for this workload.", "Compare alternatives using cost, latency, and quality evaluation.", "Small token volume alone does not establish task complexity or acceptable quality."))
    return insights


def _insight(trace: TraceDocument, kind: str, severity: str, description: str, evidence: dict[str, Any], impact: str, suggestion: str, limitation: str = "Rule-based signal; investigate in context.") -> dict[str, Any]:
    return {"insight_type": kind, "severity": severity, "trace_id": trace.trace_id, "description": description, "evidence": evidence, "potential_impact": impact, "suggested_optimization": suggestion, "confidence": limitation}


def summarize_traces(traces: list[TraceDocument]) -> dict[str, Any]:
    known_tokens = [trace.total_tokens if trace.total_tokens is not None else sum(call.total_tokens or 0 for call in trace.llm_calls) for trace in traces if trace.total_tokens is not None or (trace.llm_calls and all(call.total_tokens is not None for call in trace.llm_calls))]
    costs: list[float] = []
    trends: dict[str, dict[str, float | int]] = defaultdict(lambda: {"tokens": 0, "cost": 0.0, "latency_ms": 0, "llm_calls": 0, "executions": 0})
    for trace in traces:
        call_costs = [call.cost if call.cost is not None else estimate_call_cost(call.provider, call.model, call.input_tokens, call.output_tokens) for call in trace.llm_calls]
        trace_cost = trace.cost if trace.cost is not None else (sum(v for v in call_costs if v is not None) if call_costs and all(v is not None for v in call_costs) else None)
        trace_tokens = trace.total_tokens if trace.total_tokens is not None else (sum(call.total_tokens or 0 for call in trace.llm_calls) if trace.llm_calls and all(call.total_tokens is not None for call in trace.llm_calls) else None)
        if trace_cost is not None:
            costs.append(trace_cost)
        bucket = trends[trace.created_at.strftime("%Y-%m-%d")]
        bucket["tokens"] += trace_tokens or 0
        bucket["cost"] += trace_cost or 0
        bucket["latency_ms"] += trace.latency_ms
        bucket["llm_calls"] += len(trace.llm_calls) or 1
        bucket["executions"] += 1
    all_insights = [insight for trace in traces for insight in analyze_trace(trace)]
    comparable: dict[tuple[str, str], list[TraceDocument]] = defaultdict(list)
    for trace in traces:
        comparable_tokens = trace.total_tokens if trace.total_tokens is not None else (sum(call.total_tokens or 0 for call in trace.llm_calls) if trace.llm_calls and all(call.total_tokens is not None for call in trace.llm_calls) else None)
        if comparable_tokens is not None:
            comparable[(trace.project_id, trace.prompt.strip().lower())].append(trace)
    for group in comparable.values():
        group.sort(key=lambda trace: trace.created_at)
        for previous, current in zip(group, group[1:]):
            previous_tokens = previous.total_tokens if previous.total_tokens is not None else sum(call.total_tokens or 0 for call in previous.llm_calls)
            current_tokens = current.total_tokens if current.total_tokens is not None else sum(call.total_tokens or 0 for call in current.llm_calls)
            if previous_tokens and current_tokens >= previous_tokens * 1.5:
                increase = (current_tokens - previous_tokens) / previous_tokens * 100
                all_insights.append(_insight(current, "token_consumption_increase", "medium", "Token use increased between executions with the same project and prompt.", {"previous_trace_id": previous.trace_id, "previous_total_tokens": previous_tokens, "current_total_tokens": current_tokens, "increase_percent": round(increase, 1)}, "A sustained increase may raise operating cost.", "Compare prompt versions, output length, and execution configuration.", "Exact prompt and project matching is a limited proxy for comparability; response quality is not evaluated."))
    return {"execution_count": len(traces), "total_tokens": sum(known_tokens), "known_token_traces": len(known_tokens), "total_estimated_cost": sum(costs), "known_cost_traces": len(costs), "average_tokens_per_execution": sum(known_tokens) / len(known_tokens) if known_tokens else None, "average_execution_latency_ms": sum(trace.latency_ms for trace in traces) / len(traces) if traces else None, "total_llm_calls": sum(len(trace.llm_calls) if trace.llm_calls else 1 for trace in traces), "detected_inefficiencies": len(all_insights), "trends": [{"date": key, **value} for key, value in sorted(trends.items())], "insights": all_insights}
