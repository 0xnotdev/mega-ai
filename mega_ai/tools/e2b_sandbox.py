from mega_ai.core.schemas import ToolResult, CodeExecutionResult
from mega_ai.tools.failure import tool_contract

@tool_contract("e2b_sandbox")
async def execute_code(code: str, timeout: int = 30) -> ToolResult:
    if not code or len(code.strip()) == 0:
        raise ValueError("Code cannot be empty")

    # Stable mock sandbox for development/testing
    result = CodeExecutionResult(
        stdout=f"[MOCK] Executed: {code[:50]}...",
        stderr="",
        exit_code=0
    )

    return ToolResult(
        success=True,
        data=result.model_dump()
    )
