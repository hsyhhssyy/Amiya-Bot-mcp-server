#src/adapters/mcp/app.py
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from src.adapters.mcp.mcp_tools.arknights_glossary import register_glossary_tool
from src.adapters.mcp.mcp_tools.operator_basic import register_operator_basic_tool

def register_asgi(app: FastAPI):

    # 挂载 FastMCP 的 SSE 应用到 FastAPI 的 /mcp 路径下
    # "amiya-mcp": {
    #   "transportType":"sse",
    #   "url": "http://localhost:9000/mcp/sse"
    # }
    mcp = FastMCP("明日方舟知识库")

    register_glossary_tool(mcp,app)
    register_operator_basic_tool(mcp,app)

    app.mount("/mcp", mcp.sse_app())
