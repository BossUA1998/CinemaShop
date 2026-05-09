import inspect
import functools
from typing import Optional, Iterable

from sqlalchemy.ext.asyncio import AsyncSession


def rollback_decorator(
    error_to_raise: Optional[Exception] = None,
    exceptions: Optional[Iterable[Exception]] = None,
):
    def inner(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"{func.__name__} is not an async function")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            catch = tuple(exceptions) if exceptions else Exception
            try:
                db = kwargs.get("db") or next(
                    (arg for arg in args if isinstance(arg, AsyncSession)), None
                )
                if not db:
                    raise TypeError(
                        f"{func.__name__} must have an AsyncSession argument"
                    )
                return await func(*args, **kwargs)
            except catch:
                await db.rollback()
                if error_to_raise:
                    raise error_to_raise
                raise

        return wrapper

    return inner
