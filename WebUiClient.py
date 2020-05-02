import logging

from NetUtils import Node
from MultiClient import Context


class WebUiClient(Node):
    def __init__(self):
        super().__init__()

    @staticmethod
    def build_message(msg_type: str, content: dict) -> dict:
        return {'type': msg_type, 'content': content}

    def log_info(self, message, *args, **kwargs):
        self.broadcast_all(self.build_message('info', message))
        logging.info(message, *args, **kwargs)

    def log_warning(self, message, *args, **kwargs):
        self.broadcast_all(self.build_message('warning', message))
        logging.warning(message, *args, **kwargs)

    def log_error(self, message, *args, **kwargs):
        self.broadcast_all(self.build_message('error', message))
        logging.error(message)

    def log_critical(self, message, *args, **kwargs):
        self.broadcast_all(self.build_message('critical', message))
        logging.critical(message, *args, **kwargs)

    def send_chat_message(self, message):
        self.broadcast_all(self.build_message('chat', message))

    def send_connection_status(self, ctx: Context):
        self.broadcast_all(self.build_message('connections', {
            'snes': ctx.snes_state,
            'server': 1 if ctx.server is not None and not ctx.server.socket.closed else 0,
        }))

    def poll_for_server_ip(self):
        self.broadcast_all(self.build_message('serverAddress', {}))

    def notify_item_sent(self, finder, recipient, item, location):
        self.broadcast_all(self.build_message('itemSent', {
            'finder': finder,
            'recipient': recipient,
            'item': item,
            'location': location,
        }))

    def notify_item_found(self, finder: str, item: str, location: str):
        self.broadcast_all(self.build_message('itemFound', {
            'finder': finder,
            'item': item,
            'location': location,
        }))

    def send_hint(self, finder, recipient, item, location):
        self.broadcast_all(self.build_message('hint', {
            'finder': finder,
            'recipient': recipient,
            'item': item,
            'location': location,
        }))


class WaitingForUiException(Exception):
    pass
