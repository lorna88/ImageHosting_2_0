import os
import cgi
from urllib.parse import parse_qs
from uuid import uuid4
from PIL import Image

from loguru import logger

from AdvancedHandler import AdvancedHTTPRequestHandler
from DBManager import DBManager
from settings import IMAGES_PATH, \
    ALLOWED_EXTENSIONS, MAX_FILE_SIZE, NGINX_ADDRESS, STATIC_PATH


class ImageHostingHandler(AdvancedHTTPRequestHandler):
    server_version = 'Image Hosting Server v0.2'

    def __init__(self, request, client_address, server):
        self.db = DBManager()
        super().__init__(request, client_address, server)

    def get_images(self):
        """Handle GET request to retrieve the list of image filenames in JSON format."""
        logger.info(self.headers.get('Query-String'))
        query_components = parse_qs(self.headers.get('Query-String'))
        page = int(query_components.get('page', ['1'])[0])
        images = self.db.get_images(page)

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

    def post_upload(self):
        """Handle POST request to upload an image."""
        logger.info(f'POST {self.path}')
        content_length = int(self.headers.get('Content-Length'))
        if content_length > MAX_FILE_SIZE:
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
        orig_name, ext = os.path.splitext(form['image'].filename)
        ext = ext.lower()

        if ext not in ALLOWED_EXTENSIONS:
            logger.error('Unsupported file extension')
            self.send_error(400, 'Unsupported file Extension')
            return

        image_id = uuid4()
        image_name = f'{image_id}{ext}'
        image_path = f'{IMAGES_PATH}{image_name}'
        file_size_kb = round(content_length / 1024)
        self.db.add_image(image_id, orig_name, file_size_kb, ext)
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
            'href="?"': f'href="/{image_path}"',
            'src="?"': f'src="/{image_path}"',
            'value="?"': f'value="http://{NGINX_ADDRESS[0]}:{NGINX_ADDRESS[1]}/{image_path}"'
        }
        html_strings = open(f'{STATIC_PATH}success.html', 'r', encoding='utf-8').read()
        for old, new in str_for_replace.items():
            html_strings = html_strings.replace(old, new)

        logger.info(f'Upload success: {image_name}')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_strings.encode('utf-8'))

    def delete_image(self, image_id):
        logger.info(f'Try to delete image {image_id}')
        filename, ext = os.path.splitext(image_id)
        if not filename:
            logger.warning('Filename header not found')
            self.send_error(404, 'Filename header not found')
            return
        self.db.delete_image(filename)
        image_path = os.path.join(IMAGES_PATH, f'{filename}{ext}')
        if not os.path.exists(image_path):
            logger.warning('Image not found')
            self.send_error(404, 'Image not found')
        os.remove(image_path)
        logger.info(f'Delete success: {image_path}')
        self.send_json({'Success': 'Image deleted'})