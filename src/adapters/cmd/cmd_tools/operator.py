
import logging

from ....app.context import AppContext
from ....domain.services.operator_basic import get_operator_basic_core, OperatorNotFoundError
from ....helpers.renderer import render_with_best_renderer
from ..registery import register_command

logger = logging.getLogger(__name__)

@register_command("operator")
async def cmd_operator(ctx: AppContext, args: str) -> str:
    """
    查询干员信息
    用法: operator <干员名> [prefix]
    例子: operator 阿米娅
    """
    if not args:
        return "❌ 请提供干员名称\n用法: operator <干员名> [prefix]"
    
    parts = args.split(maxsplit=1)
    operator_name = parts[0]
    operator_name_prefix = parts[1] if len(parts) > 1 else ""
    
    try:
        logger.info(f"查询干员: {operator_name_prefix}{operator_name}")
        
        result = get_operator_basic_core(ctx, operator_name, operator_name_prefix)
        
        # 使用渲染器格式化输出
        payload = render_with_best_renderer(
            ctx, 
            "operator_basic", 
            result, 
            ensure_ascii=False
        )
        
        return f"✅ 查询结果：\n{payload}"
        
    except OperatorNotFoundError as e:
        return f"❌ {str(e)}"
    except Exception as e:
        logger.exception("查询干员信息失败")
        return f"❌ 查询失败: {e}"


@register_command("glossary")
async def cmd_glossary(ctx: AppContext, args: str) -> str:
    """
    查询术语解释
    用法: glossary <术语名>
    例子: glossary 攻击力
    """
    if not args:
        return "❌ 请提供术语名称\n用法: glossary <术语名>"
    
    try:
        if not ctx.data_repository:
            return "❌ 数据仓库未初始化"
        
        bundle = ctx.data_repository.get_bundle()
        
        if bundle.tables.get("local_glossary") is None:
            return "❌ 术语库不可用"
        
        glossary = bundle.tables["local_glossary"]
        query_term = args.strip()
        
        # 模糊匹配术语
        matched_terms = {}
        for term_name, term_info in glossary.items():
            if query_term.lower() in term_name.lower() or term_name.lower() in query_term.lower():
                matched_terms[term_name] = term_info
        
        if not matched_terms:
            return f"❌ 未找到相关术语: {query_term}"
        
        result = "✅ 查询结果：\n"
        for term_name, term_info in matched_terms.items():
            result += f"\n📌 {term_name}:\n"
            if isinstance(term_info, dict):
                result += str(term_info)
            else:
                result += str(term_info)
        
        return result
        
    except Exception as e:
        logger.exception("查询术语失败")
        return f"❌ 查询失败: {e}"