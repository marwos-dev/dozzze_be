import threading
from typing import Dict, Any, Type


class SingletonMeta(type):
    """Thread-safe implementation of Singleton pattern using metaclass."""
    _instances: Dict[Type, Any] = {}
    _lock: threading.RLock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        # First check without lock (for performance)
        if cls not in cls._instances:
            with cls._lock:
                # Second check with lock (thread-safe)
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]