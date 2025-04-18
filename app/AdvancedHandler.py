"""HTTP request handler with using Router object for routing requests"""
import json
from http.server import BaseHTTPRequestHandler

from loguru import logger

from Router import Router


class AdvancedHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler with using Router object for routing requests"""

    def __init__(self, request, client_address, server):
        """Initialize the handler with routing for GET and POST requests."""
        self.default_response = lambda: self.send_error(404, 'Not found')
        self.router = Router()
        super().__init__(request, client_address, server)

    def send_html(self, data: str,
                  code: int = 200,
                  headers: dict = None) -> None:
        """Send the response as html"""
        self.send_response(code)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        if headers:
            for header, value in headers.items():
                self.send_header(header, value)
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))

    def send_json(self, response: dict, code: int = 200,
                  headers: dict = None) -> None:
        """Send the response as json"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        if headers:
            for header, value in headers.items():
                self.send_header(header, value)
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self) -> None:
        """Handle GET requests by routing to the appropriate handler."""
        logger.info(f'GET {self.path}')
        handler, kwargs = self.router.resolve('GET', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for GET {self.path}')
            self.default_response()

    def do_POST(self) -> None:
        """Handle POST requests by routing to the appropriate handler."""
        logger.info(f'POST {self.path}')
        handler, kwargs = self.router.resolve('POST', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for POST {self.path}')
            self.default_response()

    def do_DELETE(self) -> None:
        """Handle DELETE requests by routing to the appropriate handler."""
        logger.info(f'DELETE {self.path}')
        handler, kwargs = self.router.resolve('DELETE', self.path)
        if handler:
            handler(self, **kwargs)
        else:
            logger.warning(f'No handler for DELETE {self.path}')
            self.default_response()
