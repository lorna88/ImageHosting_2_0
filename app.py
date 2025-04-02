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
        self.get_routes = {
            '/upload': self.get_upload,
            '/api/images/': self.get_images,
        }
        self.post_routes = {
            '/upload': self.post_upload,
        }
        self.delete_routes = {
            '/delete': self.delete_image,
        }
        super().__init__(request, client_address, server)

    def do_GET(self):
        """Handle GET requests by routing to the appropriate handler or returning a 404 error."""
        if self.path in self.get_routes:
            self.get_routes[self.path]()
        else:
            logger.warning(f'GET 404 {self.path}')
            self.send_error(404, 'Not Found')

    def do_POST(self):
        """Handle POST requests by routing to the appropriate handler or returning a 405 error."""
        if self.path in self.post_routes:
            self.post_routes[self.path]()
        else:
            logger.warning(f'POST 405 {self.path}')
            self.send_error(405, 'Method Not Allowed')

    def do_DELETE(self):
        if self.path in self.delete_routes:
            self.delete_routes[self.path]()
        else:
            logger.warning(f'DELETE 405 {self.path}')
            self.send_error(405, 'Method Not Allowed')

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


def run():
    """Run program"""
    db.init_tables()
    logger.info(db.get_images())
    # noinspection PyTypeChecker
    httpd = HTTPServer(SERVER_ADDRESS, ImageHostingHandler)
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
