#!/usr/bin/python3
import sys, signal, os
from http.server import HTTPServer,ThreadingHTTPServer, BaseHTTPRequestHandler
from functools import partial

from modules.server.handler_exec import ExecHandler
from modules.server.handler_model import ModelHandler
from modules.server.handler_editor import EditorHandler
from modules.server.handler_blob import BlobHandler
from threading import Lock

from .common import HandlerException
import re

class HttpDispatcher:

    def __init__(self, *args, **kwargs):

        self.editor = EditorHandler()
        self.blob = BlobHandler()
        self.model = ModelHandler(self.blob)
        self.model_lock = Lock()

    def _returnRedirect(self,server):
        server.send_response(301)
        server.send_header('Location', '/editor/')
        server.end_headers()

    def _do_graph_GET(self,server):
        http_path = server.path.split("?", 1)[0]
        split_path = http_path.split("/", 2)

        operation = split_path[2]
        if server.headers.get("Upgrade", None) == "websocket":
            wsExec = ExecHandler(server, self.blob)
            op = getattr(wsExec, operation)
            res = op()
        elif hasattr(self.model, operation):
            op = getattr(self.model, operation)
            with self.model_lock:
                self.model.server = server
                res = op()
        else:
            raise HandlerException(code=404)

    def do_GET(self,server):
        
        server.close_connection = True
        http_path = server.path.split("?",1)[0]
        split_path = http_path.split("/", 2)
        endpoint = split_path[1]

        try:
            if   re.match(r"^/$", http_path):
                return self._returnRedirect(server)
            elif re.match(r"^/graph/.+$", http_path):
                return self._do_graph_GET(server)
            elif endpoint in ["editor","src","external","css","js","imgs","style.css","examples"]:
                return self.editor.do_GET(server)
            elif re.match(r"^/blob/.+$", http_path):
                return self.blob.do_GET(server)
            else:
                raise HandlerException(code=404)

        except HandlerException as e:
            server.send_response(e.code)
            server.send_header('Content-type', 'text/html')
            server.end_headers()
            server.wfile.write(b'404 - Not Found')

    def do_POST(self,server):
        #self.model.server = server
        server.close_connection = True
        http_path = server.path.split("?", 1)[0]

        if re.match(r"^/editor/.+$", http_path):
            return self.editor.do_POST(server)


        split_path = http_path.split("/", 2)
        operation = split_path[2]
        content_length = int(server.headers['Content-Length'])
        post_data = server.rfile.read(content_length)
        if hasattr(self.model,operation):

            op = getattr(self.model,operation)
            with self.model_lock:
                self.model.server = server
                res = op(post_data)

        else:
            server.send_response(404)
            server.send_header('Content-type', 'text/html')
            server.end_headers()
            server.wfile.write(b'404 - Not Found')
        pass

class HttpServerWrapper(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, dispatcher, *args, **kwargs):
        self.dispatcher = dispatcher
        super().__init__(*args, **kwargs)

    def do_GET(self):
        return self.dispatcher.do_GET(self)

    def do_POST(self):
        return self.dispatcher.do_POST(self)

    def log_message(self,format_string,*args):
        #print("log_message",args)
        pass


def run():
    http_dispatcher = HttpDispatcher()
    http_wrapper = partial(HttpServerWrapper, http_dispatcher)
    http_server = ThreadingHTTPServer(('0.0.0.0', 8008), http_wrapper)
    print("server listening at http://localhost:8008/")

    def handler(signal_received, frame):
        print("Handler called\n")
        # http_server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)

    http_server.serve_forever()
    http_server.shutdown()

if __name__ == '__main__':
    run()


