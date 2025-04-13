"""Distributing handlers for registered routes"""
import re

from loguru import logger

from utils import SingletonMeta


class Router(metaclass=SingletonMeta):
    """Distributing handlers for registered routes"""
    def __init__(self):
        """Initialize routes dictionary"""
        self.routes = {
            'GET': {},
            'POST': {},
            'DELETE': {}
        }

    @staticmethod
    def convert_path_to_regex(path: str):
        """Convert specific path to regular expression for resolving"""
        regex = re.sub(r'<(\w+)>', r'(?P<\1>[^/]+)', path)
        regex = re.sub(r'\?(\w+)=\?', r'\?\1=(?P<\1>[0-9a-z]+)', regex)
        return f'^{regex}$'

    def add_route(self, method: str, path: str, handler: callable) -> None:
        """Add route to the dictionary"""
        regex_pattern = self.convert_path_to_regex(path)
        pattern = re.compile(regex_pattern)

        self.routes[method][pattern] = handler
        logger.info(f'Added route: {method} {path} -> {handler.__name__}')

    def resolve(self, method: str, path: str) -> tuple[callable, dict]:
        """Issue a handler for the path if it's match the regular expression"""
        if method not in self.routes:
            return None, {}
        for pattern in self.routes[method]:
            match = pattern.match(path)
            if match:
                handler = self.routes[method][pattern]
                return handler, match.groupdict()
        return None, {}
