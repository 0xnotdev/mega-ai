import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from mega_ai.db.connection import get_pool, close_pool
from mega_ai.observability.tracer import flush_worker
from mega_ai.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()

    # Start async tracer worker
    asyncio.create_task(flush_worker())

    yield

    await close_pool()


app = FastAPI(
    title="Mega AI",
    description="Real-Time Multi-Agent LLM Orchestration System",
    version="0.1.0",
    lifespan=lifespan,
)

# Register API routes
app.include_router(router)


@app.get("/")
async def health():
    return {"status": "ok", "service": "mega-ai"}