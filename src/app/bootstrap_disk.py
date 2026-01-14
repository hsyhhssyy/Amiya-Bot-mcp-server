# src/app/bootstrap.py
from pathlib import Path
from src.app.context import AppContext
from src.config.model import Config
from src.app.renderers.jinja_template_loader import JinjaTemplateLoader
from src.app.renderers.jinja_text_renderer import JinjaTextRenderer
from src.app.renderers.jinja_json_renderer import JinjaJsonRenderer
import logging
from src.data.repository.data_repository import DataRepository

logger = logging.getLogger(__name__)

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

    templates_root = cfg.ProjectRoot / "data" / "templates" 
    loader = JinjaTemplateLoader(str(templates_root))
    ctx.text_renderer = JinjaTextRenderer(loader)
    ctx.json_renderer = JinjaJsonRenderer(loader)

    return ctx