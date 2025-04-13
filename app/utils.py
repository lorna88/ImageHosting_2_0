"""Realizing a singleton pattern"""
class SingletonMeta(type):
    """Singleton class"""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Watches for using the only one copy"""
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
