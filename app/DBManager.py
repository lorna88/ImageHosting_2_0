import psycopg
from loguru import logger

from settings import IMAGES_LIMIT
from utils import SingletonMeta


class DBManager(metaclass=SingletonMeta):
    def __init__(self, dbname: str = None, user: str = None,
                 password: str = None, host: str = None, port: int = None):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = self.connect()

    def connect(self) -> psycopg.Connection:
        try:
            self.conn = psycopg.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            return self.conn
        except psycopg.Error as e:
            logger.error(f"DB connection error: {e}")

    def close(self):
        self.conn.close()

    def init_tables(self):
        self.execute_file('init_tables.sql')
        logger.info('Tables initialized')
        self.conn.commit()

    def get_images(self, page: int = 1) -> list[tuple]:
        offset = (page - 1) * IMAGES_LIMIT
        logger.info(f'Try to get images with offset {offset}')
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s", (IMAGES_LIMIT, offset))
            return cursor.fetchall()

    def execute(self, query: str):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
        except psycopg.Error as e:
            logger.error(f"Error executing query: {e}")

    def execute_file(self, filename: str):
        try:
            self.execute(open(f'./{filename}').read())
        except FileNotFoundError:
            logger.error(f"File {filename} not found")

    def add_image(self, filename: str, original_name: str, length: int, ext: str) -> None:
        logger.info(f'Try to add image {filename}')
        with self.conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO images "
                "(filename, original_name, size, file_type)"
                "VALUES (%s, %s, %s, %s)",
                (filename, original_name, length, ext)
            )
        self.conn.commit()

    def clear_images(self) -> None:
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM images")
        self.conn.commit()

    def delete_image(self, filename: str) -> None:
        logger.info(f'Try to delete image {filename}')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM images WHERE filename = %s", (filename,))
            self.conn.commit()
        except psycopg.Error as e:
            logger.error(f"Error deleting image: {e}")