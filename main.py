import asyncio
import logging
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
from .src.adapters.astrbot.operator import operator_archives_operator_query_impl

class AmiyaBotAstrbotPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        
        self._astrbot_config = config
        self.ctx: AppContext | None = None

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.ctx = await build_context_from_astrbot(self._astrbot_config)
        print("AmiyaBotAstrbotPlugin resource root:", self.ctx.cfg.GameDataPath)
    
    operator_archives_operator_query = filter.command("干员查询")(operator_archives_operator_query_impl)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
