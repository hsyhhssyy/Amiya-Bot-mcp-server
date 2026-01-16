from astrbot.api.event import filter, AstrMessageEvent

class OperatorQueryMixin:
    @filter.command("干员查询")
    async def operator_archives_operator_query(self, event: AstrMessageEvent):
        user_name = event.get_sender_name()
        message_str = event.message_str
        yield event.plain_result(
            f"Hello, {user_name}, 你发了 {message_str}!"
        )
