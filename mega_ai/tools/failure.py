import time, functools
from mega_ai.core.schemas import ToolResult

def tool_contract(tool_name: str):
    """Decorator: catches ALL exceptions, returns ToolResult"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> ToolResult:
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                result.latency_ms = int((time.time() - start) * 1000)
                return result
            except TimeoutError as e:
                return ToolResult(
                    success=False, error_code="TIMEOUT",
                    error_message=str(e), can_retry=False,
                    latency_ms=int((time.time() - start) * 1000)
                )
            except ValueError as e:
                return ToolResult(
                    success=False, error_code="MALFORMED_INPUT",
                    error_message=str(e), can_retry=True,
                    latency_ms=int((time.time() - start) * 1000)
                )
            except Exception as e:
                return ToolResult(
                    success=False, error_code="UNKNOWN_ERROR",
                    error_message=f"{tool_name}: {str(e)}", can_retry=True,
                    latency_ms=int((time.time() - start) * 1000)
                )
        return wrapper
    return decorator
