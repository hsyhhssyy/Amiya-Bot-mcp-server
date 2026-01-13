# app/bootstrap.py
from pathlib import Path
from src.app.context import AppContext
from src.config.model import Config
from astrbot.api import logger,AstrBotConfig

from src.data.loader.git_gamedata_maintainer import GitGameDataMaintainer
from src.data.loader.json_file_loader import JsonFileLoader
from src.data.repository.data_repository import DataRepository

async def build_context_from_astrbot(config: AstrBotConfig) -> AppContext:
    cfg = Config()
    cfg.load_from_astrbot_config(config)

    ctx = AppContext(config=cfg)

    json_loader= JsonFileLoader(cfg.GameDataPath)
    maintainer = GitGameDataMaintainer(cfg.GameDataRepo, Path(cfg.GameDataPath).parent)
    data_repo = DataRepository(
        json_loader=json_loader,
        maintainer=maintainer,
        context=ctx
    )
    await data_repo.ensure_ready()

    ctx.data_repository = data_repo

    return ctx
