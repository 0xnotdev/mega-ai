import json
from mega_ai.core.schemas import SynthesisResult, ProvenanceSentence, AgentID, CritiqueResult, RetrievalResult
from mega_ai.core.prompts import SYNTHESIS_PROMPT
from mega_ai.core.config import settings
import litellm

async def run_synthesis(
    query: str,
    retrieval: RetrievalResult,
    critique: CritiqueResult,
) -> SynthesisResult:
    context = {
        "query": query,
        "retrieval_answer": retrieval.answer,
        "citations": [c.model_dump() for c in retrieval.citations],
        "flagged_claims": [c.model_dump() for c in critique.claim_scores if c.flagged],
        "contradictions": critique.contradictions_found,
    }

    messages = [
        {"role": "system", "content": SYNTHESIS_PROMPT},
        {"role": "user", "content": json.dumps(context)}
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        max_tokens=2000,
    )

    data = json.loads(response.choices[0].message.content)

    provenance = [ProvenanceSentence(**p) for p in data.get("provenance_map", [])]

    return SynthesisResult(
        final_answer=data.get("final_answer", ""),
        provenance_map=provenance,
        contradictions_resolved=data.get("contradictions_resolved", [])
    )
