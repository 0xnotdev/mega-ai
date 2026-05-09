from mega_ai.core.schemas import ToolResult
from mega_ai.tools.failure import tool_contract
from mega_ai.db.connection import get_pool

ALLOWED_TABLES = {"jobs", "eval_runs", "eval_results", "documents"}

async def nl_to_sql(natural_query: str) -> str:
    """Convert natural language to safe read-only SQL."""
    q = natural_query.lower()
    if "eval" in q and "score" in q:
        return "SELECT * FROM eval_results ORDER BY created_at DESC LIMIT 10"
    elif "job" in q or "status" in q:
        return "SELECT id, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10"
    elif "document" in q or "chunk" in q:
        return "SELECT id, content FROM documents LIMIT 5"
    else:
        return "SELECT * FROM jobs LIMIT 5"

@tool_contract("db_lookup")
async def db_lookup(natural_query: str) -> ToolResult:
    if not natural_query:
        raise ValueError("Query cannot be empty")
    sql = await nl_to_sql(natural_query)
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)
        return ToolResult(
            success=True,
            data={"rows": [dict(r) for r in rows], "sql": sql, "count": len(rows)}
        )
        