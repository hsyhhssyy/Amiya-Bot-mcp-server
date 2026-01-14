if __name__ == "__main__":
    from .src.entrypoints.uvicorn_host import uvicorn_main
    uvicorn_main()
else:
    from .src.adapters.astrbot.plugin import MyPlugin as RealPlugin
    class MyPlugin(RealPlugin):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
