# src/entrypoints/uvicorn_host.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn

import asyncio
import logging

from src.app.bootstrap import build_context_from_disk
from src.adapters.mcp.app import register_asgi
from src.app.context import AppContext

log = logging.getLogger("asset")


async def _periodic_update_loop(app: FastAPI, interval_seconds: int = 15 * 60):
    while True:
        await asyncio.sleep(interval_seconds)

        ctx = getattr(app.state, "ctx", None)
        if not isinstance(ctx, AppContext):
            continue
        if not ctx.data_repository:
            continue

        try:
            await ctx.data_repository.update_and_refresh()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("data_repository.update failed")


def uvicorn_main():
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        ctx = await build_context_from_disk()
        app.state.ctx = ctx

        task = asyncio.create_task(_periodic_update_loop(app, interval_seconds=15 * 60))

        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(lifespan=lifespan)

    register_asgi(app)

    @app.get("/rest/status")
    async def status():
        return {"status": "ok"}

    uvicorn.run(app, host="0.0.0.0", port=9000)
