import uuid
from fastapi import APIRouter, HTTPException
from mega_ai.core.schemas import QueryRequest, QueryResponse, ApprovalRequest, ErrorResponse
from mega_ai.api.sse import stream_query
from mega_ai.db.connection import get_pool
import json

router = APIRouter()

@router.post("/query", response_model=None)
async def submit_query(req: QueryRequest):
    job_id = str(uuid.uuid4())

    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO jobs (id, status, user_query) VALUES ($1, $2, $3)",
            job_id,
            "processing",
            req.query
        )

    return await stream_query(job_id, req.query, req.context_budget)

@router.get("/trace/{job_id}")
async def get_trace(job_id: str):
    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM execution_traces WHERE job_id=$1 ORDER BY timestamp ASC",
            job_id
        )

    if not rows:
        raise HTTPException(
            404,
            detail={
                "error_code": "NOT_FOUND",
                "message": "Job not found",
                "job_id": job_id
            }
        )

    return {
        "job_id": job_id,
        "spans": [dict(r) for r in rows]
    }

@router.get("/eval/latest")
async def get_latest_eval():
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM eval_runs ORDER BY timestamp DESC LIMIT 1"
        )

    if not row:
        return {"message": "No eval runs yet"}

    return dict(row)

@router.post("/eval/approve/{proposal_id}")
async def approve_proposal(proposal_id: str, req: ApprovalRequest):
    pool = await get_pool()

    status = "approved" if req.approved else "rejected"

    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE prompt_proposals SET status=$1, reviewer_note=$2, reviewed_at=NOW() WHERE id=$3",
            status,
            req.reviewer_note,
            proposal_id
        )

    return {
        "proposal_id": proposal_id,
        "status": status
    }

@router.post("/eval/run")
async def trigger_eval():
    from evaluations.harness import run_eval
    import asyncio

    asyncio.create_task(run_eval())

    return {"message": "Eval started in background"}