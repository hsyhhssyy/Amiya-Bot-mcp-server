import sys

IS_MCP = "mcp" in sys.argv

if __name__ == "__main__" and IS_MCP:
    # 只有使用参数 mcp 启动时，才走 MCP（uvicorn）入口
    from src.entrypoints.uvicorn_host import uvicorn_main
    uvicorn_main()
else:
    try:
        from src.adapters.astrbot.plugin import MyPlugin  # noqa: F401
    except Exception:
        MyPlugin = None  # 仅作为占位，不做初始化
