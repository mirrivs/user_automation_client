# lib/cancellable_futures/decorators.py
from functools import wraps

from lib.cancellable_futures import get_executor


def with_pool(fn):
    """Inject the current CancellableThreadPoolExecutor as the first argument."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        pool = get_executor()
        return fn(pool, *args, **kwargs)

    return wrapper
