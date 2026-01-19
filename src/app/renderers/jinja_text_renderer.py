from __future__ import annotations

from src.app.renderers.types import Renderer,RenderOutput
from src.app.renderers.jinja_template_loader import JinjaTemplateLoader
from src.domain.types import QueryResult
import logging

logger = logging.getLogger(__name__)

class JinjaTextRenderer(Renderer):
    def __init__(self, loader: JinjaTemplateLoader):
        self.loader = loader
        self.kind = "text"

    def render(self, template_name: str, result: QueryResult) -> RenderOutput:
        ctx = {"r": result}
        text = self.loader.render_by_kind(
            kind="text", template_name=template_name, ext="txt", ctx=ctx
        )
        return RenderOutput(mime="text/plain; charset=utf-8", payload=text)
