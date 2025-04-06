import re
from loguru import logger

from utils import SingletonMeta

# logger.add('logs/router.log',
#            format='[{time:YYYY-MM-DD HH:mm:ss}] {level}: {message}',
#            level='INFO')

class Router(metaclass=SingletonMeta):
    def __init__(self):
        self.routes = {
            'GET': {},
            'POST': {},
            'DELETE': {}
        }

    @staticmethod
    def convert_path_to_regex(path: str):
        regex = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
        return f'^{regex}$'

    def add_route(self, method: str, path: str, handler: callable) -> None:
        regex_pattern = self.convert_path_to_regex(path)
        pattern = re.compile(regex_pattern)
        self.routes[method][pattern] = handler
        logger.info(f'Added route: {method} {path} -> {handler.__name__}')

    def resolve(self, method: str, path: str) -> tuple[callable, dict]:
        if method not in self.routes:
            return None, {}
        for pattern in self.routes[method]:
            match = pattern.match(path)
            if match:
                handler = self.routes[method][pattern]
                return handler, match.groupdict()
        return None, {}