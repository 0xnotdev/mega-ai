class MegaAIError(Exception):
    def __init__(self, message: str, error_code: str, job_id: str = None):
        self.message = message
        self.error_code = error_code
        self.job_id = job_id
        super().__init__(message)

class BudgetExceededError(MegaAIError):
    def __init__(self, agent_id: str, used: int, budget: int):
        super().__init__(
            message=f"{agent_id} exceeded budget: {used} > {budget} tokens",
            error_code="BUDGET_EXCEEDED"
        )

class ToolFailureError(MegaAIError):
    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            message=f"Tool {tool_name} failed: {reason}",
            error_code="TOOL_FAILURE"
        )

class SchemaValidationError(MegaAIError):
    def __init__(self, agent_id: str, detail: str):
        super().__init__(
            message=f"Agent {agent_id} produced invalid output: {detail}",
            error_code="SCHEMA_VALIDATION_ERROR"
        )
