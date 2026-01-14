if __name__ == "__main__":
    from .src.entrypoints.uvicorn_host import uvicorn_main
    uvicorn_main()
else:
    from .src.adapters.astrbot.plugin import MyPlugin
