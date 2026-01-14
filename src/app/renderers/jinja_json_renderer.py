from __future__ import annotations

import json

from ...app.renderers.types import RenderOutput
from ...app.renderers.jinja_template_loader import JinjaTemplateLoader
from ...app.renderers.types import Renderer
from ...domain.types import QueryResult


class JinjaJsonRenderer(Renderer):
    """
    使用 Jinja2 模板渲染 JSON（模板输出 JSON 字符串，render() 返回 dict/list）
    """

    def __init__(self, loader: JinjaTemplateLoader):
        self.loader = loader
        self.kind = "jinja_json"

    def render(self, template_name: str, result: QueryResult) -> RenderOutput:
        # 约定：json/<template>.json.j2
        relpath = f"json/{template_name}.json.j2"
        rendered = self.loader.render(relpath, {"r": result}).strip()

        try:
            payload = json.loads(rendered)
        except json.JSONDecodeError as e:
            # 让错误信息更可读（模板经常因为逗号/引号出错）
            msg = (
                f"JSON 模板渲染结果不是合法 JSON: {relpath}\n"
                f"错误: {e}\n"
                f"渲染结果片段(前500字):\n{rendered[:500]}"
            )
            raise ValueError(msg) from e

        return RenderOutput(
            mime="application/json; charset=utf-8",
            payload=payload,
        )
