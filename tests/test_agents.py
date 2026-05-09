import pytest
from mega_ai.agents.decomposition import run_decomposition
from mega_ai.agents.retrieval import run_retrieval
from mega_ai.core.schemas import DecompositionResult, RetrievalResult

@pytest.mark.asyncio
async def test_decomposition_returns_schema():
    result = await run_decomposition("Explain quantum computing and its applications")
    assert isinstance(result, DecompositionResult)
    assert len(result.subtasks) > 0

@pytest.mark.asyncio
async def test_retrieval_multi_hop():
    result = await run_retrieval("What is quantum entanglement?")
    assert isinstance(result, RetrievalResult)
    assert result.hops_performed >= 2
