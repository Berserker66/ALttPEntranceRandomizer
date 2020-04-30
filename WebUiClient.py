import asyncio
import json

from NetUtils import Node
from MultiClient import Context


class WebUiClient(Node):
    def __init__(self):
        super().__init__()

    @staticmethod
    def build_message(msg_type: str, content: dict) -> dict:
        return {'type': msg_type, 'content': content}

    async def send_error_message(self, message):
        self.broadcast_all(self.build_message('error', message))

    async def send_chat_message(self, message):
        self.broadcast_all(self.build_message('chat', message))

    async def send_connection_status(self, ctx: Context):
        self.broadcast_all(self.build_message('connections', {
            'snes': ctx.snes_state,
            'server': 1 if ctx.server is not None and not ctx.server.socket.closed else 0,
        }))

    async def send_item_check(self, finder, findee, item, location):
        self.broadcast_all(self.build_message('item-found', {
            'finder': finder,
            'findee': findee,
            'item': item,
            'location': location,
        }))
