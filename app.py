"""Frameworkless backend for image hosting"""
import cgi
import json
from http.server import HTTPServer, BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from os import getenv, listdir, remove
from os.path import isfile, join, splitext, exists
from urllib.parse import parse_qs
from uuid import uuid4
from PIL import Image

from loguru import logger
from DBManager import DBManager
from Router import Router

SERVER_ADDRESS = ('0.0.0.0', 8000)
NGINX_ADDRESS = ('localhost', 8080)
ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif')
ALLOWED_LENGTH = 5 * 1024 * 1024
UPLOAD_DIR = 'images'

logger.add('logs/app.log', format="[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}")

db = DBManager(getenv('POSTGRES_DB'),
                getenv('POSTGRES_USER'),
                getenv('POSTGRES_PASSWORD'),
                getenv('POSTGRES_HOST'),
                getenv('POSTGRES_PORT'))


class ImageHostingHandler(BaseHTTPRequestHandler):
    """HTTP request handler for image hosting"""

    server_version = 'Image Hosting Server/0.1'

    def __init__(self, request, client_address, server):
        """Initialize the handler with routing for GET and POST requests."""
        self.default_response = lambda: self.send_error(404, 'Method not allowed')
        self.router = Router()
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET requests by routing to the appropriate handler or returning a 404 error."""
        logger.info(f'GET {self.path}')
        handler = self.router.resolve('GET', self.path)
        if handler:
            handler(self)
        else:
            logger.warning(f'No handler for GET {self.path}')
            self.default_response()

    def do_POST(self):
        """Handle POST requests by routing to the appropriate handler or returning a 405 error."""
        logger.info(f'POST {self.path}')
        handler = self.router.resolve('POST', self.path)
        if handler:
            handler(self)
        else:
            logger.warning(f'No handler for POST {self.path}')
            self.default_response()

    def do_DELETE(self):
        logger.info(f'DELETE {self.path}')
        handler = self.router.resolve('DELETE', self.path)
        if handler:
            handler(self)
        else:
            logger.warning(f'No handler for DELETE {self.path}')
            self.default_response()

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

    def get_images(self):
        """Handle GET request to retrieve the list of image filenames in JSON format."""
        logger.info(self.headers.get('Query-String'))
        query_components = parse_qs(self.headers.get('Query-String'))
        page = int(query_components.get('page', ['1'])[0])
        images = db.get_images(page)

        logger.info(images)
        images_json = []
        for image in images:
            image = {
                'filename': image[1],
                'original_name': image[2],
                'size': image[3],
                'upload_date': image[4].strftime('%Y-%m-%d %H:%M:%S'),
                'file_type': image[5]
            }
            images_json.append(image)

        self.send_json({
            'images': images_json
        })

    def get_upload(self):
        """Handle GET request to render the upload page."""
        logger.info(f'GET {self.path}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(open('upload.html', 'rb').read())

    def post_upload(self):
        """Handle POST request to upload an image."""
        logger.info(f'POST {self.path}')
        content_length = int(self.headers.get('Content-Length'))
        if content_length > ALLOWED_LENGTH:
            logger.error('Payload Too Large')
            self.send_error(413, 'Payload Too Large')
            return

        # noinspection PyTypeChecker
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        data = form['image'].file
        orig_name, ext = splitext(form['image'].filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            logger.error('Unsupported file extension')
            self.send_error(400, 'Unsupported file Extension')
            return

        image_id = uuid4()
        image_name = f'{image_id}{ext}'
        image_path = f'{UPLOAD_DIR}/{image_name}'
        file_size_kb = round(content_length / 1024)
        db.add_image(image_id, orig_name, file_size_kb, ext)
        logger.info(f'File {image_name} uploaded')
        with open(image_path, 'wb') as f:
            f.write(data.read())

        try:
            im = Image.open(image_path)
            im.verify()
        except (IOError, SyntaxError) as e:
            logger.error(f'Invalid file: {e}')
            self.send_error(400, 'Invalid file')
            return

        # paste links on image into html document
        str_for_replace = {
            'href="?"': f'href="{image_path}"',
            'src="?"': f'src="{image_path}"',
            'value="?"': f'value="http://{NGINX_ADDRESS[0]}:{NGINX_ADDRESS[1]}/{image_path}"'
        }
        html_strings = open('success.html', 'r', encoding='utf-8').read()
        for old, new in str_for_replace.items():
            html_strings = html_strings.replace(old, new)

        logger.info(f'Upload success: {image_name}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_strings.encode('utf-8'))

    def delete_image(self):
        image_id, ext = splitext(self.headers.get('Filename'))
        logger.info(f'Try to delete image {image_id}')
        if not image_id:
            logger.warning('Filename header not found')
            self.send_error(404, 'Filename header not found')
            return
        db.delete_image(image_id)
        image_path = f'{UPLOAD_DIR}/{image_id}{ext}'
        if not exists(image_path):
            logger.warning('Image not found')
            self.send_error(404, 'Image not found')
        remove(image_path)
        logger.info(f'Delete success: {image_path}')
        self.wfile.write(json.dumps({'Success': 'Image deleted'}).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=ImageHostingHandler):
    """Run program"""
    db.init_tables()

    router = Router()
    router.add_route('GET', r'^\/upload$', handler_class.get_upload)
    router.add_route('GET', r'^\/api\/images\/$', handler_class.get_images)
    router.add_route('POST', r'^\/upload$', handler_class.post_upload)
    router.add_route('DELETE', r'^\/delete\/(.*)$', handler_class.delete_image)
    logger.info(db.get_images())
    # noinspection PyTypeChecker
    httpd = server_class(SERVER_ADDRESS, handler_class)
    # noinspection PyBroadException
    try:
        logger.info(f'Serving at http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}')
        httpd.serve_forever()
    except Exception:
        pass
    finally:
        logger.info('Server stopped')
        httpd.server_close()


if __name__ == '__main__':
    run()
