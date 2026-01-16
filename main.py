from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger,AstrBotConfig

from .src.app.context import AppContext

class MyPlugin(Star):
    def __init__(self, context: Context,config: AstrBotConfig):
        super().__init__(context)
        self._astrbot_config = config
        self.ctx: AppContext | None = None

    async def terminate(self):
        '''可选择实现 terminate 函数，当插件被卸载/停用时会调用。'''