import json, asyncio
from langgraph.graph import StateGraph, END
from mega_ai.graph.state import GraphState
from mega_ai.agents.decomposition import run_decomposition
from mega_ai.agents.retrieval import run_retrieval
from mega_ai.agents.critique import run_critique
from mega_ai.agents.synthesis import run_synthesis
from mega_ai.core.config import settings
import litellm

async def emit(state: GraphState, event_type: str, data: dict):
    q = state.get("event_queue")
    if q:
        await q.put({"event": event_type, "data": data})

async def orchestrator_node(state: GraphState) -> GraphState:
    await emit(state, "status", {"agent": "Orchestrator", "action": "deciding route"})

    has_decomp = state.get("decomposition_result") is not None
    has_retrieval = state.get("retrieval_result") is not None
    has_critique = state.get("critique_result") is not None

    if not has_decomp:
        target = "decomposition"
    elif not has_retrieval:
        target = "retrieval"
    elif not has_critique:
        target = "critique"
    else:
        target = "synthesis"

    state["routing_target"] = target
    return state

async def decomposition_node(state: GraphState) -> GraphState:
    await emit(state, "status", {"agent": "Decomposition", "action": "running"})

    result = await run_decomposition(state["user_query"])

    state["decomposition_result"] = result.model_dump()
    state["routing_target"] = "orchestrator"

    return state

async def retrieval_node(state: GraphState) -> GraphState:
    await emit(state, "status", {"agent": "Retrieval", "action": "multi-hop search"})

    result = await run_retrieval(state["user_query"])

    state["retrieval_result"] = result.model_dump()
    state["routing_target"] = "orchestrator"

    return state

async def critique_node(state: GraphState) -> GraphState:
    await emit(state, "status", {"agent": "Critique", "action": "scoring claims"})

    content = state.get("retrieval_result", {}).get("answer", "")

    result = await run_critique(content)

    state["critique_result"] = result.model_dump()
    state["routing_target"] = "orchestrator"

    return state

async def synthesis_node(state: GraphState) -> GraphState:
    await emit(state, "status", {"agent": "Synthesis", "action": "building provenance map"})

    from mega_ai.core.schemas import RetrievalResult, CritiqueResult

    retrieval = RetrievalResult(**state["retrieval_result"])
    critique = CritiqueResult(**state["critique_result"])

    result = await run_synthesis(state["user_query"], retrieval, critique)

    state["synthesis_result"] = result.model_dump()
    state["status"] = "completed"

    await emit(state, "done", {"answer": result.final_answer})

    return state

def route(state: GraphState) -> str:
    target = state.get("routing_target", "orchestrator")

    if state.get("status") == "completed":
        return END

    return target

def build_graph():
    g = StateGraph(GraphState)

    g.add_node("orchestrator", orchestrator_node)
    g.add_node("decomposition", decomposition_node)
    g.add_node("retrieval", retrieval_node)
    g.add_node("critique", critique_node)
    g.add_node("synthesis", synthesis_node)

    g.set_entry_point("orchestrator")

    g.add_conditional_edges("orchestrator", route)

    g.add_edge("decomposition", "orchestrator")
    g.add_edge("retrieval", "orchestrator")
    g.add_edge("critique", "orchestrator")
    g.add_edge("synthesis", END)

    return g.compile()

compiled_graph = build_graph()