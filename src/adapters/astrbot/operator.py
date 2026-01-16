
import logging
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult

from ...domain.services.operator import search_operator_by_name

from ...domain.types import QueryResult
from ...app.context import AppContext
from ...domain.services.operator_basic import get_operator_basic_core, OperatorNotFoundError
from ...domain.models.operator import Operator
from ...helpers.renderer import render_with_best_renderer
from ...helpers.gamedata.search import search_source_spec, build_sources

logger = logging.getLogger(__name__)

async def operator_archives_operator_query(ctx: AppContext, event: AstrMessageEvent, query_str: str):
    
        

        yield event.plain_result(
            f"Hello, {user_name}, 你发了 {message_str}!"
        )