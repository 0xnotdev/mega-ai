import json
import litellm

from mega_ai.core.schemas import DecompositionResult, SubTask
from mega_ai.core.prompts import DECOMPOSITION_PROMPT
from mega_ai.core.config import settings


async def run_decomposition(
    query: str,
    context: str = ""
) -> DecompositionResult:

    messages = [
        {
            "role": "system",
            "content": DECOMPOSITION_PROMPT
        },
        {
            "role": "user",
            "content": f"Query: {query}\nContext: {context}"
        }
    ]

    response = await litellm.acompletion(
        model="groq/llama-3.1-8b-instant",
        messages=messages,
        api_key=settings.groq_api_key,
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=300,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    # Handle multiple possible response formats safely
    if isinstance(data, list):
        subtasks_data = data
        dependency_graph = {}
        ambiguity_flags = []
    else:
        subtasks_data = data.get("subtasks") or data.get("tasks", [])
        dependency_graph = data.get("dependency_graph", {})
        ambiguity_flags = data.get("ambiguity_flags", [])

    subtasks = [
        SubTask(
            task_id=str(t.get("task_id", i)),
            description=t.get("description", ""),
            depends_on=[str(d) for d in t.get("depends_on", [])],
            task_type=t.get("task_type", "general"),
            status=t.get("status", "pending"),
        )
        for i, t in enumerate(subtasks_data)
    ]

    return DecompositionResult(
        subtasks=subtasks,
        dependency_graph=dependency_graph,
        ambiguity_flags=ambiguity_flags,
    )