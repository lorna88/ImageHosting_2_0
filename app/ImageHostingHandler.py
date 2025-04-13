"""HTTP request handler for image hosting"""
import os
import cgi
from uuid import uuid4
from PIL import Image

from loguru import logger

from AdvancedHandler import AdvancedHTTPRequestHandler
from DBManager import DBManager
from settings import IMAGES_PATH, \
    ALLOWED_EXTENSIONS, MAX_FILE_SIZE, NGINX_ADDRESS, STATIC_PATH,\
    IMAGES_LIMIT


class ImageHostingHandler(AdvancedHTTPRequestHandler):
    """HTTP request handler for image hosting"""
    server_version = 'Image Hosting Server v0.2'

    def __init__(self, request, client_address, server):
        """Initialize the handler with using db manager"""
        self.db = DBManager()
        super().__init__(request, client_address, server)

    def get_images(self, page: str) -> None:
        """Handle GET request to retrieve the list of image objects in JSON format.
        Images list is selected from database for specific page number"""
        page = int(page)
        images_count = self.db.get_images_count()
        last_page = (images_count - 1) // IMAGES_LIMIT + 1
        page = max(page, 1)
        page = min(page, last_page)

        images = self.db.get_images(page)
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

        images_json = {'images': images_json,
                       'page': page,
                       'last_page': last_page == page}
        self.send_json(images_json)

    # noinspection PyTypeChecker
    def post_upload(self) -> None:
        """Handle POST request to upload an image."""
        length = int(self.headers.get('Content-Length'))
        if length > MAX_FILE_SIZE:
            logger.error('File Too Large')
            self.send_error(413, 'File Too Large')
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD': 'POST'}
        )

        data = form['image'].file
        orig_name, ext = os.path.splitext(form['image'].filename)
        ext = ext.lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.error('File type not allowed')
            self.send_error(400, 'File type not allowed')
            return

        filename = uuid4()
        image_path = os.path.join(IMAGES_PATH, f'{filename}{ext}')


        if not self.db.add_image(filename, orig_name, round(length / 1024), ext):
            logger.error('Error inserting image')
            self.send_error(500, 'Error inserting image')
            return

        logger.info(f'File {filename}{ext} uploaded')
        with open(image_path, 'wb') as file:
            file.write(data.read())

        try:
            Image.open(image_path).verify()
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
        with open(os.path.join(STATIC_PATH, 'success.html'), 'r', encoding='utf-8') as html:
            html_strings = html.read()
            for old, new in str_for_replace.items():
                html_strings = html_strings.replace(old, new)

            self.send_html(html_strings)

    def delete_image(self, image_id: str) -> None:
        """Handle DELETE request to delete an image by identifier."""
        logger.info(f'Try to delete image {image_id}')
        filename, ext = os.path.splitext(image_id)
        if not filename:
            logger.warning('Filename header not found')
            self.send_error(404, 'Filename header not found')
            return
        if not self.db.delete_image(filename):
            logger.error('Error deleting image')
            self.send_error(500, 'Error deleting image')
            return

        image_path = os.path.join(IMAGES_PATH, f'{filename}{ext}')
        if not os.path.exists(image_path):
            logger.warning('Image not found')
            self.send_error(404, 'Image not found')
        os.remove(image_path)
        self.send_json({'Success': 'Image deleted'})
