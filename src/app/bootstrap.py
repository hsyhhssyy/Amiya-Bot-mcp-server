# src/app/bootstrap.py
from pathlib import Path
from src.app.context import AppContext
from src.config.model import Config
# from astrbot.api import logger,AstrBotConfig

from src.data.repository.data_repository import DataRepository

# async def build_context_from_astrbot(config: AstrBotConfig) -> AppContext:
#     cfg = Config()
#     cfg.load_from_astrbot_config(config)

#     project_root = Path(__file__).resolve().parents[2] 
#     cfg.ProjectRoot = project_root

#     ctx = AppContext(config=cfg)

#     data_repo = DataRepository(
#         cfg=cfg,
#     )
#     await data_repo.startup_prepare(True)

#     ctx.data_repository = data_repo

#     return ctx

async def build_context_from_disk() -> AppContext:
    cfg = Config()
    cfg.load_from_disk()
    
    project_root = Path(__file__).resolve().parents[2] 
    cfg.ProjectRoot = project_root

    ctx = AppContext(cfg=cfg)

    data_repo = DataRepository(
        cfg=cfg,
    )
    await data_repo.startup_prepare(True)

    ctx.data_repository = data_repo

    return ctx