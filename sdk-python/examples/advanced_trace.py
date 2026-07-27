from tracewell import Tracewell


client = Tracewell(
    api_key="demo",
    base_url="http://localhost:8000",
    project_id="support-agent",
)

result = client.trace(
    prompt="Summarize the latest support ticket.",
    response="The customer needs help changing their billing email.",
    latency_ms=842,
    provider="openai",
    model="gpt-4.1-mini",
    input_tokens=32,
    output_tokens=18,
    cost=0.00014,
)

print(f"Sent trace: {result.trace_id}")
