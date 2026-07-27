from tracewell import Tracewell


client = Tracewell(api_key="demo")

result = client.trace(
    prompt="Hello",
    response="Hi",
    latency_ms=230,
)

print(result.trace_id)
