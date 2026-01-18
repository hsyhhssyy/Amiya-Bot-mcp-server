
import logging

from src.domain.services.operator import search_operator_by_name
from src.app.context import AppContext
from src.domain.services.operator_basic import OperatorNotFoundError
from src.domain.models.operator import Operator
from src.adapters.cmd.registery import register_command
from src.helpers.gamedata.search import search_source_spec, build_sources

logger = logging.getLogger(__name__)


@register_command("op")
async def cmd_operator(ctx: AppContext, args: str) -> str:
    """
    查询干员信息
    用法: op <干员名> [prefix]
    例子: op 阿米娅
    """
    if not args:
        return "❌ 请提供干员名称\n用法: op <干员名> [prefix]"

    parts = args.split(maxsplit=1)
    operator_name = parts[0]
    operator_name_prefix = parts[1] if len(parts) > 1 else ""

    try:
        logger.info(f"查询干员: {operator_name_prefix}{operator_name}")

        operator_query = operator_name_prefix + operator_name

        search_sources = build_sources(ctx.data_repository.get_bundle(), source_key=["name"])
        search_results = search_source_spec(operator_query, sources=search_sources)

        # 注意：你原本的判断是 len(search_results.matches) > 1
        # 更稳：只看 name key 的命中
        if not search_results:
            raise OperatorNotFoundError(f"未找到干员: {operator_query}")

        name_matches = search_results.by_key("name")
        if len(name_matches) != 1:
            matched_names = [m.matched_text for m in search_results.matches if m.key == "name"]
            return f"❌ 找到多个匹配的干员名称: {', '.join(matched_names)}，请提供更精确的名称。"

        op: Operator = name_matches[0].value

        # 领域查询（保留）
        result = search_operator_by_name(ctx, op.name)

        # 生成 payload_key：要求包含 version
        bundle = ctx.data_repository.get_bundle()
        bundle_version = getattr(bundle, "version", None) or getattr(bundle, "hash", None) or "v0"

        payload_key = f"operator:{op.name}:{bundle_version}"

        # ✅ 交给 CardService：如果磁盘已有 png，就直接命中返回；否则现场渲染
        artifact = await ctx.card_service.get(
            template="operator_info",
            payload_key=payload_key,
            payload=result,      # 这里直接传 QueryResult
            format="png",
            params=None,         # 你也可以传 viewport/full_page 等覆写配置
        )

        # 目前你还没接“发图”，先返回路径（或返回 html）
        return f"✅ 已生成干员卡片：{op.name}\n📌 缓存文件：{artifact.path}"

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