import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def render_with_best_renderer(
    context: Any,
    template: str,
    data: Any,
    *,
    ensure_ascii: bool = False,
) -> str:
    """
    渲染优先级：
      1) context.json_renderer.render(template, data).payload -> json.dumps
      2) context.text_renderer.render(template, data).payload -> str
      3) json.dumps(data)

    任何渲染异常：记录日志并返回兜底 json（如果兜底也失败则返回固定错误字符串）
    """
    try:
        json_renderer = getattr(context, "json_renderer", None)
        if json_renderer is not None:
            rendered = json_renderer.render(template, data)
            payload = getattr(rendered, "payload", rendered)
            return json.dumps(payload, ensure_ascii=ensure_ascii)

        text_renderer = getattr(context, "text_renderer", None)
        if text_renderer is not None:
            rendered = text_renderer.render(template, data)
            payload = getattr(rendered, "payload", rendered)
            # text_renderer 通常就应该返回 str；这里强制转一下避免类型不一致
            return payload if isinstance(payload, str) else str(payload)

        return json.dumps(data, ensure_ascii=ensure_ascii)

    except Exception:
        logger.exception("渲染失败，回退到 raw json")
        try:
            return json.dumps(data, ensure_ascii=ensure_ascii)
        except Exception:
            logger.exception("raw json 序列化也失败")
            return "渲染失败"
