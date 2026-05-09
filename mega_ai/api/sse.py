import asyncio, json
from sse_starlette.sse import EventSourceResponse
from mega_ai.graph.orchestrator import compiled_graph
from mega_ai.graph.state import GraphState

async def stream_query(job_id: str, query: str, budget: int):
    queue = asyncio.Queue()

    initial_state: GraphState = {
        "job_id": job_id,
        "user_query": query,
        "routing_target": None,
        "context_budget": budget,
        "tokens_used": 0,
        "message_history": [],
        "decomposition_result": None,
        "retrieval_result": None,
        "critique_result": None,
        "synthesis_result": None,
        "tool_call_log": [],
        "execution_trace": [],
        "policy_violations": [],
        "status": "processing",
        "event_queue": queue,
        "iteration_count": 0,
    }

    async def run_graph():
        await compiled_graph.ainvoke(initial_state)
        await queue.put(None)

    asyncio.create_task(run_graph())

    async def generator():
        yield {
            "event": "status",
            "data": json.dumps({
                "job_id": job_id,
                "status": "started"
            })
        }

        while True:
            item = await queue.get()

            if item is None:
                break

            yield {
                "event": item["event"],
                "data": json.dumps(item["data"])
            }

    return EventSourceResponse(generator())