# src/app/bootstrap.py
from pathlib import Path
import logging

from src.app.renderers.jinja_html_renderer import JinjaHtmlRenderer
from src.app.context import AppContext
from src.app.config import Config
from src.app.card_service import CardService
from src.data.repository.data_repository import DataRepository

logger = logging.getLogger(__name__)

async def build_context_from_disk() -> AppContext:
    cfg = Config()
    cfg.load_from_disk()
    
    project_root = Path(__file__).resolve().parents[2] 
    cfg.ProjectRoot = project_root


    data_repo = DataRepository(
        cfg=cfg,
    )
    await data_repo.startup_prepare(True)

    card_service = CardService(cfg)

    ctx = AppContext(
        cfg=cfg,
        data_repository=data_repo,
        card_service=card_service
    )

    return ctx