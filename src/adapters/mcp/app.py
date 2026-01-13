#src/adapters/mcp/app.py
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP


def register_asgi(app: FastAPI):

    # 挂载 FastMCP 的 SSE 应用到 FastAPI 的 /mcp 路径下
    # "amiya-mcp": {
    #   "transportType":"sse",
    #   "url": "http://localhost:9000/mcp/sse"
    # }
    mcp = FastMCP("明日方舟知识库")
    app.mount("/mcp", mcp.sse_app())
