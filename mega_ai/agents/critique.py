import json
import litellm

from mega_ai.core.schemas import CritiqueResult, ClaimScore
from mega_ai.core.prompts import CRITIQUE_PROMPT
from mega_ai.core.config import settings


async def run_critique(
    content_to_critique: str
) -> CritiqueResult:

    messages = [
        {
            "role": "system",
            "content": CRITIQUE_PROMPT
        },
        {
            "role": "user",
            "content": (
                f"Content to critique:\n"
                f"{content_to_critique}"
            )
        }
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=400,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    raw_claims = data.get("claim_scores", [])

    claim_scores = []

    for c in raw_claims:

        if isinstance(c, dict):
            claim_scores.append(
                ClaimScore(
                    claim=str(c.get("claim", "")),
                    confidence=float(
                        c.get("confidence", 0.5)
                    ),
                    flagged=bool(
                        c.get("flagged", False)
                    ),
                    justification=str(
                        c.get("justification", "")
                    ),
                )
            )

    overall = (
        sum(c.confidence for c in claim_scores)
        / max(len(claim_scores), 1)
    )

    return CritiqueResult(
        claim_scores=claim_scores,
        overall_confidence=round(overall, 3),
        contradictions_found=data.get(
            "contradictions_found",
            []
        ),
    )