import http.server
import socketserver
import os
import threading
from functools import partial

import Utils

webthread = None

PORT = 5050

Handler = partial(http.server.SimpleHTTPRequestHandler, directory=Utils.local_path(os.path.join("webUi", "public")))


def start_server(on_start=lambda: None):
    global webthread
    try:
        server = socketserver.TCPServer(("", PORT), Handler)
    except OSError:  # in most cases "Only one usage of each socket address (protocol/network address/port) is normally permitted"
        import logging
        logging.exception("Could not bind port for webui client. Console client should still work.")
    else:
        print("serving at port", PORT)
        on_start()
        webthread = threading.Thread(target=server.serve_forever).start()
        return True
    return False

if __name__ == "__main__":
    start_server()
