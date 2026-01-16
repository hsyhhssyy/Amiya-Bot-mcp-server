# src/app/context.py
from dataclasses import dataclass
from typing import Optional

from src.config.model import Config
from src.data.repository.data_repository import DataRepository
from src.app.renderers.types import Renderer

@dataclass(slots=True)
class AppContext:
    cfg: Config
    data_repository: DataRepository
    text_renderer : Optional[Renderer] = None
    json_renderer : Optional[Renderer] = None
    html_renderer : Optional[Renderer] = None
