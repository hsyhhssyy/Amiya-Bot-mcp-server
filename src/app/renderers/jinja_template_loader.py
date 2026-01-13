from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)

class JinjaTemplateLoader:
    def __init__(self, template_root: str):
        self.env = Environment(
            loader=FileSystemLoader(template_root),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, relpath: str, ctx: dict) -> str:
        return self.env.get_template(relpath).render(**ctx)
