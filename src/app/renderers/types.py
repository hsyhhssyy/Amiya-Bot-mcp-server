from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol
from src.domain.types import QueryResult


@dataclass
class RenderOutput:
    mime: str
    payload: Any


class Renderer(Protocol):
    """
    所有 renderer 的统一协议
    """
    kind: str

    def render(self, template_name: str, result: QueryResult) -> RenderOutput:
        ...

