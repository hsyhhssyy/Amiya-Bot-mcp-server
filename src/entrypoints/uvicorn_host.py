# src/entrypoints/uvicorn_host.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

from src.app.bootstrap import build_context_from_disk
from src.adapters.mcp.app import register_asgi

def uvicorn_main():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ctx = await build_context_from_disk()
        app.state.ctx = ctx
        yield
        # 这里可以做 shutdown 清理（如果需要）

    app = FastAPI(lifespan=lifespan)

    register_asgi(app)
    
    @app.get("/rest/status")
    async def status():
        return {"status": "ok"}

    uvicorn.run(app, host="0.0.0.0", port=9000)
