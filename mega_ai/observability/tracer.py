import asyncio, hashlib, json
from datetime import datetime
from mega_ai.db.connection import get_pool

_queue: asyncio.Queue = asyncio.Queue()

async def log_span(job_id: str, agent_id: str, event_type: str,
                   payload: dict, latency_ms: int = 0, tokens: int = 0):
    span = {
        "timestamp": datetime.utcnow().isoformat(),
        "job_id": job_id,
        "agent_id": agent_id,
        "event_type": event_type,
        "input_hash": hashlib.sha256(json.dumps(payload).encode()).hexdigest()[:16],
        "latency_ms": latency_ms,
        "tokens_used": tokens,
        "policy_violations": [],
        "payload": payload,
    }

    await _queue.put(span)

async def flush_worker():
    """Background task: drains queue into PostgreSQL."""
    pool = await get_pool()

    while True:
        span = await _queue.get()

        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO execution_traces
                    (job_id, agent_id, event_type, input_hash, latency_ms, tokens_used, payload)
                    VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                span["job_id"],
                span["agent_id"],
                span["event_type"],
                span["input_hash"],
                span["latency_ms"],
                span["tokens_used"],
                json.dumps(span["payload"]))

        except Exception as e:
            print(f"Tracer flush error: {e}")