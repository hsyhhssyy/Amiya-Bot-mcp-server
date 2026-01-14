# src/app/bootstrap.py
from pathlib import Path
from astrbot.api import logger,AstrBotConfig
from ..app.context import AppContext
from ..config.model import Config
from ..app.renderers.jinja_template_loader import JinjaTemplateLoader
from ..app.renderers.jinja_text_renderer import JinjaTextRenderer
from ..app.renderers.jinja_json_renderer import JinjaJsonRenderer
import logging
from ..data.repository.data_repository import DataRepository

logger = logging.getLogger(__name__)

async def build_context_from_astrbot(config: AstrBotConfig) -> AppContext:
    cfg = Config()
    cfg.load_from_astrbot_config(config)

    project_root = Path(__file__).resolve().parents[2] 
    cfg.ProjectRoot = project_root

    ctx = AppContext(cfg=cfg)

    # data_repo = DataRepository(
    #     cfg=cfg,
    # )
    # await data_repo.startup_prepare(True)
    # ctx.data_repository = data_repo

    return ctx
