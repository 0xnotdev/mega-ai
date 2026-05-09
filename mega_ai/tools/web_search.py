from mega_ai.core.schemas import ToolResult, SearchResult
from mega_ai.tools.failure import tool_contract

@tool_contract("web_search")
async def web_search(query: str, max_results: int = 5) -> ToolResult:
    if not query or len(query.strip()) == 0:
        raise ValueError("Query cannot be empty")

    # Stub returns deterministic fake results
    results = [
        SearchResult(
            url=f"https://example.com/result-{i}",
            title=f"Result {i} for: {query[:40]}",
            snippet=f"This source discusses {query[:30]}... with relevant details about the topic including facts and citations.",
            relevance_score=round(1.0 - (i * 0.15), 2)
        )
        for i in range(min(max_results, 5))
    ]

    if not results:
        return ToolResult(
            success=False, error_code="EMPTY_RESULTS",
            error_message="No results found", can_retry=True
        )

    return ToolResult(
        success=True,
        data={"results": [r.model_dump() for r in results], "query": query}
    )