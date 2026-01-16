import asyncio
import logging
from pathlib import Path
import sys
import argparse

from .src.entrypoints.command_line import cmd_main

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-C",
        "--custom-mode",
        action="store_true",
        help="启动时进入命令行模式"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    # 可以用环境变量 / 全局变量 / 配置传递
    if args.custom_mode:
        print("🚀 使用 -C 启动，进入命令行模式")
        asyncio.run(cmd_main())
        sys.exit(0)
    else:
        from .src.entrypoints.uvicorn_host import uvicorn_main
        uvicorn_main()
        sys.exit(0)

logger = logging.getLogger(__name__)

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger,AstrBotConfig

from .src.app.bootstrap_astrbot import build_context_from_astrbot
from .src.app.context import AppContext

from .src.domain.services.operator import search_operator_by_name

from .src.domain.types import QueryResult
from .src.app.context import AppContext
from .src.domain.services.operator_basic import get_operator_basic_core, OperatorNotFoundError
from .src.domain.models.operator import Operator
from .src.helpers.renderer import render_with_best_renderer
from .src.helpers.gamedata.search import search_source_spec, build_sources

class AmiyaBotAstrbotPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        
        self._astrbot_config = config
        self.ctx: AppContext | None = None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.ctx = await build_context_from_astrbot(self._astrbot_config)
        print("AmiyaBotAstrbotPlugin resource root:", self.ctx.cfg.GameDataPath)
    
    @filter.command("查询")
    async def operator_archives_operator_query(self, event: AstrMessageEvent):

        if not self.ctx or not self.ctx.cfg.ProjectRoot:
            yield event.plain_result("❌ 插件未初始化完成，请稍后再试。")
            return

        query_str = event.message_str.strip()

        try:
            logger.info(f"查询干员: {query_str}")
            
            search_sources = build_sources(self.ctx.data_repository.get_bundle(), source_key=["name"])
            search_results = search_source_spec(
                query_str,
                sources=search_sources
            )

            if not search_results:
                yield event.plain_result("未找到干员!")
                return
            elif len(search_results.matches) > 1:
                # 交互式选择结果
                matched_names = [m.matched_text for m in search_results.matches if m.key == "name"]
                yield event.plain_result(
                    f"❌ 找到多个匹配的干员名称: {', '.join(matched_names)}，请提供更精确的名称。"
                )
                return
            
            op: Operator = search_results.by_key("name")[0].value

            result = search_operator_by_name(self.ctx, op.name)

            # 从磁盘读取template
            template_file = self.ctx.cfg.ProjectRoot / "data" / "templates" / "html" / "operator_info.html"

            if not template_file.exists():
                yield event.plain_result(f"模板文件{template_file}不存在，无法渲染结果!")
                return

            TMPL = template_file.read_text(encoding="utf-8")

            url = await self.html_render(TMPL, result.data, options={}) # 第二个参数是 Jinja2 的渲染数据
            yield event.image_result(url)
            return
        except OperatorNotFoundError as e:
            yield event.plain_result("未找到干员!")
            return
        except Exception as e:
            logger.exception("查询干员信息失败")
            yield event.plain_result("未找到干员!")
            return

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
