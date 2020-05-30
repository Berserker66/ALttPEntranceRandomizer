import http.server
import socketserver
import os
import threading
from functools import partial

import Utils

webthread = None

PORT = 5050

Handler = partial(http.server.SimpleHTTPRequestHandler, directory=Utils.local_path(os.path.join("webUi", "public")))


def start_server():
    global webthread
    threading.Thread(target=run_server).start()


def run_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()


if __name__ == "__main__":
    start_server()
