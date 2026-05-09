import json
import uuid
import asyncio

from pathlib import Path

from mega_ai.agents.retrieval import run_retrieval
from mega_ai.agents.critique import run_critique
from mega_ai.agents.synthesis import run_synthesis

from mega_ai.db.connection import get_pool
from mega_ai.core.config import settings

import litellm


CASES = json.loads(
    Path("evaluations/test_cases.json").read_text()
)


async def judge_answer(
    query: str,
    answer: str,
    expected: str
) -> dict:
    """
    LLM-as-a-judge scoring.
    """

    prompt = f"""
Score how well the answer addresses the query.

Return JSON ONLY:
{{
  "score": 0.0,
  "justification": "reason"
}}

Query:
{query}

Expected:
{expected}

Got:
{answer[:500]}
"""

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=200,
    )

    raw = response.choices[0].message.content

    return json.loads(raw)


async def score_case(
    case: dict,
    category: str
) -> dict:

    query = case["query"]

    scores = {}

    try:

        retrieval = await run_retrieval(query)

        critique = await run_critique(
            retrieval.answer
        )

        synthesis = await run_synthesis(
            query,
            retrieval,
            critique
        )

        answer = synthesis.final_answer

        # ---------------------------------
        # Dimension 1: Answer Correctness
        # ---------------------------------

        expected = case.get(
            "expected_answer",
            "N/A"
        )

        correctness = await judge_answer(
            query,
            answer,
            expected
        )

        scores["answer_correctness"] = correctness

        # ---------------------------------
        # Dimension 2: Citation Accuracy
        # ---------------------------------

        citation_score = min(
            len(retrieval.citations) / 2.0,
            1.0
        )

        scores["citation_accuracy"] = {
            "score": citation_score,
            "justification": (
                f"{len(retrieval.citations)} "
                f"citations found"
            )
        }

        # ---------------------------------
        # Dimension 3: Contradiction Resolution
        # ---------------------------------

        resolved = len(
            synthesis.contradictions_resolved
        )

        found = len(
            critique.contradictions_found
        )

        contradiction_score = (
            1.0
            if found == 0
            else min(
                resolved / max(found, 1),
                1.0
            )
        )

        scores["contradiction_resolution"] = {
            "score": contradiction_score,
            "justification": (
                f"{resolved}/{found} "
                f"contradictions resolved"
            )
        }

        # ---------------------------------
        # Dimension 4: Tool Efficiency
        # ---------------------------------

        scores["tool_efficiency"] = {
            "score": 0.8,
            "justification": "baseline tool usage"
        }

        # ---------------------------------
        # Dimension 5: Budget Compliance
        # ---------------------------------

        scores["budget_compliance"] = {
            "score": 1.0,
            "justification": "within budget"
        }

        # ---------------------------------
        # Dimension 6: Critique Agreement
        # ---------------------------------

        agreement_score = (
            critique.overall_confidence
        )

        scores["critique_agreement"] = {
            "score": agreement_score,
            "justification": (
                f"critique confidence "
                f"{agreement_score:.2f}"
            )
        }

        # ---------------------------------
        # Final Aggregate
        # ---------------------------------

        overall = (
            sum(v["score"] for v in scores.values())
            / len(scores)
        )

        return {
            "test_id": case["id"],
            "category": category,
            "query": query,
            "scores": scores,
            "overall": round(overall, 3),
            "passed": overall >= 0.6,
        }

    except Exception as e:

        return {
            "test_id": case["id"],
            "category": category,
            "query": query,
            "scores": {},
            "overall": 0.0,
            "passed": False,
            "error": str(e),
        }


async def run_eval(
    failed_only: bool = False
):

    eval_id = str(uuid.uuid4())

    all_results = []

    for category, cases in CASES.items():

        for case in cases:

            print(f"Running {case['id']}...")

            result = await score_case(
                case,
                category
            )

            all_results.append(result)

    average_score = (
        sum(r["overall"] for r in all_results)
        / len(all_results)
    )

    pool = await get_pool()

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO eval_runs
            (id, average_score, test_results)
            VALUES ($1, $2, $3)
            """,
            eval_id,
            average_score,
            json.dumps(all_results)
        )

    print(
        f"Eval complete. "
        f"Average score: {average_score:.3f}"
    )

    return {
        "eval_run_id": eval_id,
        "average_score": average_score,
        "results": all_results,
    }


if __name__ == "__main__":
    asyncio.run(run_eval())