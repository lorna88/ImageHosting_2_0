"""Managing requests to database"""
import psycopg
from loguru import logger

from settings import IMAGES_LIMIT
from utils import SingletonMeta


class DBManager(metaclass=SingletonMeta):
    """Managing requests to database"""
    def __init__(self, dbname: str = None, user: str = None,
                 password: str = None, host: str = None, port: int = None):
        """Initialize the db manager with connect parameters"""
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.conn = self.connect()

    def connect(self) -> psycopg.Connection:
        """Connect to database"""
        try:
            self.conn = psycopg.connect(
                dbname=self.dbname,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
        except psycopg.Error as e:
            logger.error(f"DB connection error: {e}")
        return self.conn

    def close(self) -> None:
        """Close the connection to database"""
        self.conn.close()

    def init_tables(self) -> None:
        """Creates tables for keeping images data"""
        self.execute_file('init_tables.sql')
        logger.info('Tables initialized')
        self.conn.commit()

    def get_images(self, page: int = 1) -> list[tuple]:
        """Select images for specific page"""
        offset = (page - 1) * IMAGES_LIMIT
        logger.info(f'Try to get images with offset {offset}')
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT * FROM images ORDER BY upload_time DESC LIMIT %s OFFSET %s",
                           (IMAGES_LIMIT, offset))
            return cursor.fetchall()

    def execute(self, query: str) -> None:
        """Execute the query"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
        except psycopg.Error as e:
            logger.error(f"Error executing query: {e}")

    def execute_file(self, filename: str) -> None:
        """Execute the query from file"""
        try:
            self.execute(open(f'./{filename}').read())
        except FileNotFoundError:
            logger.error(f"File {filename} not found")

    def add_image(self, filename: str, original_name: str, length: int, ext: str) -> bool:
        """Add data for new image into the table"""
        logger.info(f'Try to add image {filename}')
        try:
            with self.conn.cursor() as cursor:
                # noinspection PyTypeChecker
                cursor.execute(
                    "INSERT INTO images "
                    "(filename, original_name, size, file_type)"
                    "VALUES (%s, %s, %s, %s)",
                    (filename, original_name, length, ext)
                )
            self.conn.commit()
            return True
        except psycopg.Error as e:
            logger.error(f"Error inserting image: {e}")
            self.conn.rollback()
            return False

    def clear_images(self) -> None:
        """Delete all data from image table"""
        with self.conn.cursor() as cursor:
            cursor.execute("DELETE FROM images")
        self.conn.commit()

    def delete_image(self, filename: str) -> bool:
        """Delete one image from the table with specific filename"""
        logger.info(f'Try to delete image {filename}')
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM image WHERE filename = %s", (filename,))
            self.conn.commit()
            return True
        except psycopg.Error as e:
            logger.error(f"Error deleting image: {e}")
            self.conn.rollback()
            return False

    def get_images_count(self) -> int:
        """Get a count of images in table
        Used for a validation of page number"""
        with self.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM images")
            return cursor.fetchone()[0]
