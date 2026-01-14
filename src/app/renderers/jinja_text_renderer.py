from __future__ import annotations

from ...app.renderers.types import Renderer,RenderOutput
from ...app.renderers.jinja_template_loader import JinjaTemplateLoader
from ...domain.types import QueryResult
import logging

logger = logging.getLogger(__name__)

class JinjaTextRenderer(Renderer):
    """
    使用 Jinja2 模板渲染文本
    """

    def __init__(self, loader: JinjaTemplateLoader):
        self.loader = loader
        self.kind = "text"

    def render(self, template_name: str, result: QueryResult) -> RenderOutput:
        # 统一约定：text/<template>.txt.j2
        relpath = f"text/{template_name}.txt.j2"
        text = self.loader.render(relpath, {"r": result})
        return RenderOutput(
            mime="text/plain; charset=utf-8",
            payload=text,
        )
