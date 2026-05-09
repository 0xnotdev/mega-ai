import pytest, asyncio
from mega_ai.tools.web_search import web_search
from mega_ai.tools.e2b_sandbox import execute_code
from mega_ai.tools.self_reflection import self_reflect

@pytest.mark.asyncio
async def test_web_search_success():
    r = await web_search("quantum computing")
    assert r.success is True
    assert len(r.data["results"]) > 0

@pytest.mark.asyncio
async def test_web_search_empty():
    r = await web_search("")
    assert r.success is False
    assert r.error_code == "MALFORMED_INPUT"

@pytest.mark.asyncio
async def test_code_execution():
    r = await execute_code("print('hello world')")
    assert r.success is True

@pytest.mark.asyncio
async def test_self_reflect_no_history():
    r = await self_reflect([], "test")
    assert r.success is False
    assert r.error_code == "EMPTY_HISTORY"