import json
import uuid
import difflib

import litellm

from mega_ai.core.config import settings
from mega_ai.core import prompts as P
from mega_ai.db.connection import get_pool


PROMPT_REGISTRY = {
    "DecompositionAgent": "DECOMPOSITION_PROMPT",
    "RetrievalAgent": "RETRIEVAL_PROMPT",
    "CritiqueAgent": "CRITIQUE_PROMPT",
    "SynthesisAgent": "SYNTHESIS_PROMPT",
}


async def propose_rewrite(
    failed_cases: list[dict],
    worst_agent: str
) -> dict:

    prompt_name = PROMPT_REGISTRY.get(
        worst_agent,
        "DECOMPOSITION_PROMPT"
    )

    original_prompt = getattr(
        P,
        prompt_name
    )

    meta_prompt = f"""
You are a prompt optimization expert.

The following agent is underperforming:
{worst_agent}

Failed cases:
{json.dumps(failed_cases[:3], indent=2)}

Current prompt:
{original_prompt}

Your task:
1. Rewrite the prompt to improve reliability
2. Reduce ambiguity
3. Improve structured JSON adherence
4. Reduce hallucinations
5. Preserve original intent

Return JSON ONLY:
{{
  "proposed_prompt": "...",
  "justification": "what changed and why"
}}
"""

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": meta_prompt
            }
        ],
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=700,
    )

    raw = response.choices[0].message.content

    data = json.loads(raw)

    proposed_prompt = data.get(
        "proposed_prompt",
        original_prompt
    )

    justification = data.get(
        "justification",
        "No justification provided"
    )

    diff = "\n".join(
        difflib.unified_diff(
            original_prompt.splitlines(),
            proposed_prompt.splitlines(),
            fromfile="original",
            tofile="proposed",
            lineterm=""
        )
    )

    proposal_id = str(uuid.uuid4())

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO prompt_proposals
            (
                id,
                agent_id,
                original_prompt,
                proposed_prompt,
                diff_text,
                justification
            )
            VALUES ($1,$2,$3,$4,$5,$6)
            """,
            proposal_id,
            worst_agent,
            original_prompt,
            proposed_prompt,
            diff,
            justification,
        )

    return {
        "proposal_id": proposal_id,
        "agent": worst_agent,
        "diff": diff,
        "justification": justification,
    }