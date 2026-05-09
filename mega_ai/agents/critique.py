import json
from mega_ai.core.schemas import CritiqueResult, ClaimScore
from mega_ai.core.prompts import CRITIQUE_PROMPT
from mega_ai.core.config import settings
import litellm

async def run_critique(content_to_critique: str) -> CritiqueResult:
    messages = [
        {"role": "system", "content": CRITIQUE_PROMPT},
        {"role": "user", "content": f"Content to critique:\n{content_to_critique}"}
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        max_tokens=1000,
    )

    data = json.loads(response.choices[0].message.content)

    claim_scores = [ClaimScore(**c) for c in data.get("claim_scores", [])]

    overall = sum(c.confidence for c in claim_scores) / max(len(claim_scores), 1)

    return CritiqueResult(
        claim_scores=claim_scores,
        overall_confidence=round(overall, 3),
        contradictions_found=data.get("contradictions_found", [])
    )
    
