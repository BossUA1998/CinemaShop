from sqlalchemy import insert, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserGroupModel, UserGroupEnum, ActivationTokenModel
from schemas.accounts import UserRegistrationRequestSchema


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
        .where(ActivationTokenModel.user_id == User.id) # Join
        .where(User.email == email)
    )
    return db_res.rowcount == 1
