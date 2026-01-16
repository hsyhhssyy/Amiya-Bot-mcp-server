from __future__ import annotations

from src.app.renderers.types import Renderer,RenderOutput
from src.app.renderers.jinja_template_loader import JinjaTemplateLoader
from src.domain.types import QueryResult
import logging

logger = logging.getLogger(__name__)

class JinjaHtmlRenderer(Renderer):
    """
    使用 Jinja2 模板渲染文本
    """

    def __init__(self, loader: JinjaTemplateLoader):
        self.loader = loader
        self.kind = "html"

    def render(self, template_name: str, result: QueryResult) -> RenderOutput:
        # 统一约定：html/<template>.txt.j2
        relpath = f"html/{template_name}.html.j2"
        ctx = dict(result.data or {})
        ctx["r"] = result
        text = self.loader.render(relpath, ctx)
        return RenderOutput(
            mime="text/html; charset=utf-8",
            payload=text,
        )
