#src/entrypoints/uvicorn_host.py
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import uvicorn
from src.config.model import Config
from src.app.context import AppContext

from src.adapters.mcp.app import register_asgi

def uvicorn_main():
    app = FastAPI()

    cfg = Config()
    cfg.load_from_disk()

    ctx = AppContext(cfg=cfg)

    register_asgi(app,ctx)

    # 定义一个简单的状态检查路由
    @app.get("/rest/status")
    async def status():
        return {"status": "ok"}

    uvicorn.run(app, host="0.0.0.0", port=9000, log_config=logger.LOG_CONFIG)