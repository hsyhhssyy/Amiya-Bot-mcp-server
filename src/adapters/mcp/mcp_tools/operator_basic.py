import re
import logging

from typing import Annotated
from pydantic import Field

from src.adapters.mcp.mcp_tools.arknights_glossary import mark_glossary_used_terms
from src.app.context import AppContext
from src.domain.models.operator import Operator

logger = logging.getLogger("mcp_tool")
def register_operator_basic_tool(mcp, app):
    @mcp.tool(description="获取干员的基础信息和属性")
    def get_operator_basic(
        operator_name: Annotated[str, Field(description="干员名")],
        operator_name_prefix: Annotated[str, Field(description="干员名的前缀，没有则为空")] = "",
    ) -> str:
        
        logger.info(f'查询干员基础信息：{operator_name_prefix}{operator_name}')

        # 1) 基础防御：ctx / repo / bundle / tables
        if not getattr(app.state, "ctx", None):
            logger.warning("未初始化数据上下文")
            return "未初始化数据上下文"

        context: AppContext = app.state.ctx
        if not context.data_repository:
            logger.warning("数据仓库未初始化")
            return "数据仓库未初始化"
        

        bundle = context.data_repository.get_bundle()
        tables = getattr(bundle, "tables", None) or {}

        operator_id = bundle.operator_name_to_id.get(operator_name_prefix+operator_name,None)
        if not operator_id:
            logger.warning(f'未找到干员{operator_name}的资料')
            return f'未找到干员{operator_name}的资料'
        
        opt = bundle.operators.get(operator_id)

        if not opt or not isinstance(opt, Operator):
            logger.warning(f'未找到干员{operator_name}的资料')
            return f'未找到干员{operator_name}的资料'
        
        glossary_used = []

        char_name = opt.name

        opt_detail = opt.detail()

        char_desc = opt_detail.get('trait',"无描述")

        classes = opt.classes
        classes_sub = opt.classes_sub

        group = opt.group


        content = f'{char_name}\n职业：{classes_sub}（{classes}），{char_desc}\n阵营：{group}\n' + '\n'.join(
            [f'{n}：{opt_detail[k]}%s' % tables.get("attrs_unit", {}).get(k, '') for k, n in tables.get("attrs", {}).items()]
        )

        # 处理classes_glossary
        
        glossary_used += mark_glossary_used_terms(context,classes)
        glossary_used += mark_glossary_used_terms(context,classes_sub)

        talents = []

        for index, item in enumerate(opt.talents()):
            if item['talents_name']:
                text = '第%d天赋：%s，效果为%s。' % (
                    index + 1,
                    item['talents_name'],
                    item['talents_desc'],
                )

                talents.append(text)

        content += ('\n\n' + '\n'.join(talents)) if talents else ''

        if glossary_used:
            content += '\n\n涉及术语：' + '，'.join(set(glossary_used))

        logger.info(content)

        return content
