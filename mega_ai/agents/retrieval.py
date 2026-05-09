import json
import litellm

from mega_ai.core.schemas import RetrievalResult, ChunkCitation
from mega_ai.core.prompts import RETRIEVAL_PROMPT
from mega_ai.core.config import settings


async def get_mock_chunks(query: str) -> list[dict]:
    """Returns mock chunks when DB is empty."""

    return [
        {
            "chunk_id": "chunk_001",
            "content": (
                f"Source A discusses {query[:30]}: "
                "key facts about topic overview and background."
            ),
        },
        {
            "chunk_id": "chunk_002",
            "content": (
                f"Source B elaborates on {query[:30]}: "
                "specific details, statistics, and expert analysis."
            ),
        },
    ]


async def run_retrieval(query: str) -> RetrievalResult:
    chunks = await get_mock_chunks(query)

    chunks_text = json.dumps(chunks)

    messages = [
        {
            "role": "system",
            "content": RETRIEVAL_PROMPT
        },
        {
            "role": "user",
            "content": f"Query: {query}\nChunks: {chunks_text}"
        }
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=500,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    raw_citations = data.get("citations", [])

    citations = []

    for c in raw_citations:

        if isinstance(c, dict):
            citations.append(
                ChunkCitation(
                    chunk_id=str(c.get("chunk_id", "unknown")),
                    content_snippet=str(
                        c.get(
                            "content_snippet",
                            c.get("content", "")
                        )
                    ),
                    relevance_score=float(
                        c.get("relevance_score", 1.0)
                    ),
                    contributed_to=str(
                        c.get("contributed_to", query)
                    ),
                )
            )

        elif isinstance(c, str):
            citations.append(
                ChunkCitation(
                    chunk_id="unknown",
                    content_snippet=c,
                    relevance_score=1.0,
                    contributed_to=query,
                )
            )

    return RetrievalResult(
        answer=data.get("answer", ""),
        citations=citations,
        hops_performed=data.get(
            "hops_performed",
            len(chunks)
        ),
        chunks_consulted=[
            c["chunk_id"] for c in chunks
        ],
    )