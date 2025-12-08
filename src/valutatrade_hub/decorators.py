from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Dict

from .logging_config import configure_logging

logger = configure_logging()


def log_action(action: str, verbose: bool = False) -> Callable:
    """Декоратор логирования доменных операций."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Пытаемся вытащить user / username из аргументов
            user = kwargs.get("user") or (args[0] if args else None)
            username = getattr(user, "username", "unknown")
            details: Dict[str, Any] = {
                "action": action,
                "username": username,
            }
            try:
                result = func(*args, **kwargs)
                details["result"] = "OK"
                if verbose and isinstance(result, dict):
                    details.update(result)
                logger.info(str(details))
                return result
            except Exception as exc:  # пробрасываем дальше
                details["result"] = "ERROR"
                details["error_type"] = exc.__class__.__name__
                details["error_message"] = str(exc)
                logger.info(str(details))
                raise

        return wrapper

    return decorator
