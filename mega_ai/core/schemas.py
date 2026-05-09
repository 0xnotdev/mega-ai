from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────
class AgentID(str, Enum):
    ORCHESTRATOR  = "MasterOrchestrator"
    DECOMPOSITION = "DecompositionAgent"
    RETRIEVAL     = "RetrievalAgent"
    CRITIQUE      = "CritiqueAgent"
    SYNTHESIS     = "SynthesisAgent"
    COMPRESSION   = "CompressionAgent"
    META          = "MetaAgent"

class JobStatus(str, Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"

class EventType(str, Enum):
    ROUTING_DECISION = "routing_decision"
    AGENT_START      = "agent_start"
    AGENT_COMPLETE   = "agent_complete"
    TOOL_CALL        = "tool_call"
    TOOL_RESULT      = "tool_result"
    BUDGET_CHECK     = "budget_check"
    COMPRESSION      = "compression"
    POLICY_VIOLATION = "policy_violation"
    TOKEN_STREAM     = "token_stream"


# ── Tool schemas ────────────────────────────────────────
class ToolResult(BaseModel):
    success: bool
    data: Optional[dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    can_retry: bool = False
    latency_ms: int = 0

class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    relevance_score: float

class CodeExecutionResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


# ── Agent output schemas ────────────────────────────────
class SubTask(BaseModel):
    task_id: str
    description: str
    depends_on: list[str] = Field(default_factory=list)
    task_type: str
    status: str = "pending"

class DecompositionResult(BaseModel):
    subtasks: list[SubTask]
    dependency_graph: dict[str, list[str]]
    ambiguity_flags: list[str] = Field(default_factory=list)

class ChunkCitation(BaseModel):
    chunk_id: str
    content_snippet: str
    relevance_score: float
    contributed_to: str

class RetrievalResult(BaseModel):
    answer: str
    citations: list[ChunkCitation]
    hops_performed: int
    chunks_consulted: list[str]

class ClaimScore(BaseModel):
    claim_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    flagged: bool
    flag_reason: Optional[str] = None
    span_start: Optional[int] = None
    span_end: Optional[int] = None

class CritiqueResult(BaseModel):
    claim_scores: list[ClaimScore]
    overall_confidence: float = Field(ge=0.0, le=1.0)
    contradictions_found: list[str] = Field(default_factory=list)

class ProvenanceSentence(BaseModel):
    sentence: str
    source_agent: AgentID
    source_chunk_id: Optional[str] = None

class SynthesisResult(BaseModel):
    final_answer: str
    provenance_map: list[ProvenanceSentence]
    contradictions_resolved: list[str] = Field(default_factory=list)

class RoutingDecision(BaseModel):
    target_agent: AgentID
    justification: str
    estimated_tokens: int = 0


# ── Shared LangGraph state ──────────────────────────────
class SharedState(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_query: str
    routing_target: Optional[AgentID] = None
    context_budget: int = 8000
    tokens_used: int = 0
    message_history: list[dict[str, Any]] = Field(default_factory=list)
    decomposition_result: Optional[DecompositionResult] = None
    retrieval_result: Optional[RetrievalResult] = None
    critique_result: Optional[CritiqueResult] = None
    synthesis_result: Optional[SynthesisResult] = None
    tool_call_log: list[dict[str, Any]] = Field(default_factory=list)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Observability schemas ───────────────────────────────
class LogSpan(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    job_id: str
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: AgentID
    event_type: EventType
    input_hash: Optional[str] = None
    output_hash: Optional[str] = None
    latency_ms: int = 0
    token_count: int = 0
    policy_violations: list[str] = Field(default_factory=list)
    payload: dict[str, Any] = Field(default_factory=dict)


# ── Evaluation schemas ──────────────────────────────────
class EvalDimension(str, Enum):
    ANSWER_CORRECTNESS     = "answer_correctness"
    CITATION_ACCURACY      = "citation_accuracy"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"
    TOOL_EFFICIENCY        = "tool_efficiency"
    BUDGET_COMPLIANCE      = "budget_compliance"
    CRITIQUE_AGREEMENT     = "critique_agreement"

class DimensionScore(BaseModel):
    dimension: EvalDimension
    score: float = Field(ge=0.0, le=1.0)
    justification: str

class TestCaseResult(BaseModel):
    test_id: str
    category: str
    query: str
    scores: list[DimensionScore]
    overall_score: float
    passed: bool

class EvalRunSummary(BaseModel):
    eval_run_id: str
    timestamp: datetime
    test_results: list[TestCaseResult]
    average_score: float
    failed_cases: list[str]


# ── API request/response schemas ────────────────────────
class QueryRequest(BaseModel):
    query: str
    context_budget: int = 8000

class QueryResponse(BaseModel):
    job_id: str
    status: JobStatus

class ApprovalRequest(BaseModel):
    approved: bool
    reviewer_note: Optional[str] = None

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    job_id: Optional[str] = None