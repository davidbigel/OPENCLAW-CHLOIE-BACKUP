from __future__ import annotations

import functools
import inspect
import logging
from typing import Any, MutableMapping


def _wrap_function(func: Any, logger: logging.Logger) -> Any:
    if getattr(func, "__mc_instrumented__", False):
        return func

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info("function_start %s", func.__qualname__)
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception("function_error %s", func.__qualname__)
            raise

    wrapper.__mc_instrumented__ = True
    return wrapper


def instrument_module_functions(
    namespace: MutableMapping[str, Any],
    logger: logging.Logger | None = None,
    *,
    exclude: set[str] | None = None,
) -> None:
    module_name = str(namespace.get("__name__", ""))
    module_logger = logger or logging.getLogger(module_name)
    skipped = set(exclude or ())
    for name, value in list(namespace.items()):
        if name in skipped:
            continue
        if inspect.isfunction(value) and value.__module__ == module_name:
            namespace[name] = _wrap_function(value, module_logger)


def instrument_class_methods(cls: type[Any], logger: logging.Logger | None = None) -> type[Any]:
    class_logger = logger or logging.getLogger(cls.__module__)
    for name, value in list(vars(cls).items()):
        if isinstance(value, staticmethod):
            setattr(cls, name, staticmethod(_wrap_function(value.__func__, class_logger)))
            continue
        if isinstance(value, classmethod):
            setattr(cls, name, classmethod(_wrap_function(value.__func__, class_logger)))
            continue
        if inspect.isfunction(value):
            setattr(cls, name, _wrap_function(value, class_logger))
    return cls
