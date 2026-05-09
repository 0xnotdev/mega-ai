import tiktoken
from mega_ai.core.config import settings

_enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(_enc.encode(text))

def check_budget(current_tokens: int, budget: int) -> dict:
    remaining = budget - current_tokens
    ratio = current_tokens / max(budget, 1)

    return {
        "remaining": remaining,
        "used": current_tokens,
        "budget": budget,
        "ratio": round(ratio, 3),
        "needs_compression": ratio >= settings.compression_threshold,
        "violation": remaining < 0
    }

async def compress_if_needed(state: dict) -> dict:
    budget = state.get("context_budget", 8000)
    history = state.get("message_history", [])

    total_text = " ".join(str(m.get("content", "")) for m in history)

    tokens = count_tokens(total_text)

    info = check_budget(tokens, budget)

    if info["needs_compression"] and len(history) > 2:
        # Losslessly keep last 2 messages, summarize the rest
        kept = history[-2:]

        old_text = " | ".join(
            str(m.get("content", ""))[:100]
            for m in history[:-2]
        )

        compressed = [
            {
                "role": "system",
                "content": f"[COMPRESSED HISTORY]: {old_text}"
            }
        ] + kept

        state["message_history"] = compressed

    state["tokens_used"] = tokens

    return state
    