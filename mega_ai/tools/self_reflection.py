from mega_ai.core.schemas import ToolResult
from mega_ai.tools.failure import tool_contract

@tool_contract("self_reflection")
async def self_reflect(session_history: list[dict], look_for: str) -> ToolResult:
    if not session_history:
        return ToolResult(
            success=False, error_code="EMPTY_HISTORY",
            error_message="No session history to reflect on", can_retry=False
        )
    contradictions = []
    all_claims = []
    for entry in session_history:
        content = entry.get("content", "")
        if look_for.lower() in content.lower():
            all_claims.append(content[:200])
    if len(all_claims) > 1:
        contradictions.append(f"Found {len(all_claims)} references to '{look_for}'")
    return ToolResult(
        success=True,
        data={"relevant_history": all_claims, "contradictions": contradictions, "entries_scanned": len(session_history)}
    )
