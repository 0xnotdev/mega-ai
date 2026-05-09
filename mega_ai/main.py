from fastapi import FastAPI
from contextlib import asynccontextmanager
from mega_ai.db.connection import get_pool, close_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Mega AI",
    description="Real-Time Multi-Agent LLM Orchestration System",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def health():
    return {"status": "ok", "service": "mega-ai"}
