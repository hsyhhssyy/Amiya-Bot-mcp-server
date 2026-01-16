import json
import logging

from src.helpers.renderer import render_with_best_renderer
from src.app.context import AppContext
from src.domain.services.operator_basic import get_operator_basic_core, OperatorNotFoundError
from src.app.renderers.types import Renderer

logger = logging.getLogger(__name__)

def register_operator_basic_tool(mcp, app):
    @mcp.tool(description="获取干员的基础信息和属性")
    def get_operator_basic(operator_name: str, operator_name_prefix: str = "") -> str:
        logger.info(f"查询干员基础信息：{operator_name_prefix}{operator_name}")

        if not getattr(app.state, "ctx", None):
            return "未初始化数据上下文"

        context: AppContext = app.state.ctx

        try:
            result = get_operator_basic_core(context, operator_name, operator_name_prefix)
        except OperatorNotFoundError as e:
            return str(e)
        except Exception:
            logger.exception("查询失败")
            return "查询失败"

        # 优先json_renderer,然后text_renderer,然后直接json format

        payload = render_with_best_renderer(context, "operator_basic", result, ensure_ascii=False)

        logger.info(payload)

        return payload
