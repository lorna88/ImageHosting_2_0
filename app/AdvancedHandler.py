import json
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler

from loguru import logger

from Router import Router

class AdvancedHTTPRequestHandler(BaseHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        """Initialize the handler with routing for GET and POST requests."""
        self.default_response = lambda: self.send_error(404, 'Method not allowed')
        self.router = Router()
        super().__init__(request, client_address, server)

    def end_headers(self):
        """Add custom headers before ending the HTTP response headers."""
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)

    def send_json(self, response: dict, code: int = 200,
                  headers: dict = None) -> None:
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        if headers:
            for header, value in headers.items():
                self.send_header(header, value)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        """Handle GET requests by routing to the appropriate handler or returning a 404 error."""
        logger.info(f'GET {self.path}')
        handler, kwargs = self.router.resolve('GET', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for GET {self.path}')
            self.default_response()

    def do_POST(self):
        """Handle POST requests by routing to the appropriate handler or returning a 405 error."""
        logger.info(f'POST {self.path}')
        handler, kwargs = self.router.resolve('POST', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for POST {self.path}')
            self.default_response()

    def do_DELETE(self):
        logger.info(f'DELETE {self.path}')
        handler, kwargs = self.router.resolve('DELETE', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for DELETE {self.path}')
            self.default_response()