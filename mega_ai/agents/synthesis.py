import json
import litellm

from mega_ai.core.schemas import (
    SynthesisResult,
    ProvenanceSentence,
    CritiqueResult,
    RetrievalResult,
)

from mega_ai.core.prompts import SYNTHESIS_PROMPT
from mega_ai.core.config import settings


async def run_synthesis(
    query: str,
    retrieval: RetrievalResult,
    critique: CritiqueResult,
) -> SynthesisResult:

    context = {
        "query": query,
        "retrieval_answer": retrieval.answer,
        "citations": [
            c.model_dump()
            for c in retrieval.citations
        ],
        "flagged_claims": [
            c.model_dump()
            for c in critique.claim_scores
            if c.flagged
        ],
        "contradictions": critique.contradictions_found,
    }

    messages = [
        {
            "role": "system",
            "content": SYNTHESIS_PROMPT
        },
        {
            "role": "user",
            "content": json.dumps(context)
        }
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=600,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    raw_provenance = data.get(
        "provenance_map",
        []
    )

    provenance = []

    for p in raw_provenance:

        if isinstance(p, dict):
            provenance.append(
                ProvenanceSentence(
                    sentence=str(
                        p.get("sentence", "")
                    ),
                    source_agent=str(
                        p.get(
                            "source_agent",
                            "retrieval"
                        )
                    ),
                    source_chunk_id=str(
                        p.get(
                            "source_chunk_id",
                            "unknown"
                        )
                    ),
                )
            )

    return SynthesisResult(
        final_answer=data.get(
            "final_answer",
            ""
        ),
        provenance_map=provenance,
        contradictions_resolved=data.get(
            "contradictions_resolved",
            []
        ),
    )