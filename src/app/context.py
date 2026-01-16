# src/app/context.py
from dataclasses import dataclass
from typing import Optional

from ..config.model import Config
from ..data.repository.data_repository import DataRepository
from ..app.renderers.types import Renderer

@dataclass(slots=True)
class AppContext:
    cfg: Config
    data_repository: DataRepository
    text_renderer : Optional[Renderer] = None
    json_renderer : Optional[Renderer] = None
    html_renderer : Optional[Renderer] = None
