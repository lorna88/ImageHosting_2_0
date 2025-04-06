"""Frameworkless backend for image hosting"""
import os
from http.server import HTTPServer
from routes import register_routes
from settings import LOG_PATH, LOG_FILE
from settings import SERVER_ADDRESS

from loguru import logger
from DBManager import DBManager
from ImageHostingHandler import ImageHostingHandler
from Router import Router

logger.add('../logs/app.log', format="[{time: YYYY-MM-DD HH:mm:ss}] | {level} | {message}")


def run(server_class=HTTPServer, handler_class=ImageHostingHandler):
    """Run program"""
    logger.add(os.path.join(LOG_PATH, LOG_FILE),
               format='[{time:YYYY-MM-DD HH:mm:ss}] {level}: {message}',
               level='INFO')

    db = DBManager(os.getenv('POSTGRES_DB'),
                   os.getenv('POSTGRES_USER'),
                   os.getenv('POSTGRES_PASSWORD'),
                   os.getenv('POSTGRES_HOST'),
                   os.getenv('POSTGRES_PORT'))
    db.init_tables()

    router = Router()
    register_routes(router, handler_class)
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
