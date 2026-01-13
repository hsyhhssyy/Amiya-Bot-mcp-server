if __name__ == "__main__":
    from src.entrypoints.uvicorn_host import uvicorn_main
    uvicorn_main()
else:
    try:
        from src.adapters.astrbot.plugin import MyPlugin  # noqa: F401
    except Exception:
        MyPlugin = None  # 仅作为占位，别做初始化
