from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, UserGroupModel, UserGroupEnum, ActivationTokenModel
from schemas.accounts import UserRegistrationRequestSchema


async def create_new_user(db: AsyncSession, user_data: UserRegistrationRequestSchema):
    raw_user = User(**user_data.model_dump(exclude={"password"}))
    raw_user.password = user_data.password
    raw_user.group_id = await db.scalar(
        select(UserGroupModel.id)
        .where(UserGroupModel.name == UserGroupEnum.USER)
    )
    db.add(raw_user)
    await db.flush()

    return raw_user


async def create_activation_token(db: AsyncSession, token: str, user: User):
    activation_token = await db.execute(
        insert(ActivationTokenModel)
        .values(
            token=token,
            user_id=user.id,
        )
    )

async def get_user_by_activation_token(db: AsyncSession, token: str):
    return await db.scalar(
        select(User)
        .join(ActivationTokenModel)
        .where(ActivationTokenModel.token == token)
    )
