from typing import TypedDict, Optional, Any
from mega_ai.core.schemas import AgentID, JobStatus, DecompositionResult, RetrievalResult, CritiqueResult, SynthesisResult
import asyncio

class GraphState(TypedDict):
    job_id: str
    user_query: str
    routing_target: Optional[str]
    context_budget: int
    tokens_used: int
    message_history: list[dict]
    decomposition_result: Optional[dict]
    retrieval_result: Optional[dict]
    critique_result: Optional[dict]
    synthesis_result: Optional[dict]
    tool_call_log: list[dict]
    execution_trace: list[dict]
    policy_violations: list[str]
    status: str
    event_queue: Optional[Any]
    iteration_count: int