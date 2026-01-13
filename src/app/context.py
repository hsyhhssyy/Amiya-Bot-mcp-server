# src/app/context.py
from dataclasses import dataclass
from typing import Optional

from src.config.model import Config
from src.data.repository.data_repository import DataRepository


@dataclass(slots=True)
class AppContext:
    cfg: Config
    data_repository: Optional[DataRepository] = None
