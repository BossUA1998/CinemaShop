import inspect
import functools
from typing import Optional, Iterable
from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserGroupModel, UserGroupEnum, ActivationTokenModel, RefreshTokenModel
from schemas.accounts import UserRegistrationRequestSchema


def rollback_decorator(
        error_to_raise: Optional[Exception] = None,
        exceptions: Optional[Iterable[Exception]] = None,
):
    def inner(func):
        if not inspect.iscoroutinefunction(func):
            raise TypeError(f"{func.__name__} is not an async function")

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            catch = tuple(exceptions) if exceptions else (Exception,)
            try:
                db = kwargs.get("db") or next(
                    (arg for arg in args if isinstance(arg, AsyncSession)), None
                )
                if not db:
                    raise TypeError(f"{func.__name__} must have an AsyncSession argument")
                return await func(*args, **kwargs)
            except catch:
                await db.rollback()
                if error_to_raise:
                    raise error_to_raise
                raise

        return wrapper

    return inner


async def create_new_user(db: AsyncSession, user_data: UserRegistrationRequestSchema) -> User:
    raw_user = User(**user_data.model_dump(exclude={"password"}))
    raw_user.password = user_data.password
    raw_user.group_id = await db.scalar(
        select(UserGroupModel.id)
        .where(UserGroupModel.name == UserGroupEnum.USER)
    )
    db.add(raw_user)
    await db.flush()

    return raw_user


async def create_activation_token(db: AsyncSession, token: str, user: User) -> None:
    await db.execute(
        insert(ActivationTokenModel)
        .values(
            token=token,
            user_id=user.id,
        )
    )


async def get_activation_token(db: AsyncSession, token: str) -> ActivationTokenModel:
    return await db.scalar(
        select(ActivationTokenModel)
        .where(ActivationTokenModel.token == token)
    )


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    return await db.scalar(
        select(User)
        .where(User.email == email)
    )


async def get_user_by_activation_token(db: AsyncSession, token: str) -> User:
    return await db.scalar(
        select(User)
        .join(ActivationTokenModel)
        .where(ActivationTokenModel.token == token)
    )


async def delete_all_activation_tokens(db: AsyncSession, email: str) -> bool:
    db_res = await db.execute(
        delete(ActivationTokenModel)
        .where(ActivationTokenModel.user_id == User.id)  # Join
        .where(User.email == email)
    )
    return db_res.rowcount == 1


async def delete_refresh_tokens(db: AsyncSession, token: str, user_id: int = None) -> bool:
    stmt = (
        delete(RefreshTokenModel)
        .where(RefreshTokenModel.token == token)
    )
    if user_id:
        stmt = stmt.where(RefreshTokenModel.user_id == user_id)
    db_res = await db.execute(stmt)
    return db_res.rowcount == 1


async def create_refresh_token(db: AsyncSession, token: str, user: User) -> None:
    await db.execute(
        insert(RefreshTokenModel)
        .values(token=token, user_id=user.id)
    )
