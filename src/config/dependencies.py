from typing import Annotated

from fastapi import Depends, Request, HTTPException, status
from fastapi.params import Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from notifications.emails import EmailSender
from security import JWTManager

from database.session import (
    get_postgresql_db as get_db,
)


def get_settings() -> Settings:
    return Settings()


def get_email_sender(
    settings: Settings = Depends(get_settings),
) -> EmailSender:
    return EmailSender(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        path_to_templates=settings.PATH_TO_EMAIL_TEMPLATES,
        activation_email_template_name=settings.ACTIVATION_EMAIL_TEMPLATE_NAME,
        activation_complete_email_template_name=settings.ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME,
        password_email_template_name=settings.PASSWORD_RESET_TEMPLATE_NAME,
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME,
        comment_answer_template_name=settings.COMMENT_ANSWER_TEMPLATE_NAME,
        comment_reaction_template_name=settings.COMMENT_REACTION_TEMPLATE_NAME,
    )


def get_token(request: Request) -> str:
    authorization_header = request.headers.get("Authorization")

    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    scheme, _, token = authorization_header.partition(" ")

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
        )

    return token


def get_jwt_manager(settings: Settings = Depends(get_settings)) -> JWTManager:
    return JWTManager(
        access_secret_key=settings.SECRET_KEY_ACCESS,
        refresh_secret_key=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_LIFETIME,
        refresh_token_expire_days=settings.REFRESH_TOKEN_LIFETIME,
    )


def page_to_limit_offset(
    settings: Settings = Depends(get_settings), page: int = Query(default=1, ge=1)
) -> tuple[int, int]:
    limit = settings.DEFAULT_PAGE_SIZE
    offset = limit * (page - 1)

    return limit, offset


def token_data(
    raw_token: str = Depends(get_token),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
) -> dict:
    return jwt_manager.decode_access_token(token=raw_token)


DATABASE = Annotated[AsyncSession, Depends(get_db)]
TOKEN_DATA = Annotated[dict, Depends(token_data)]
LIMIT_OFFSET = Annotated[tuple[int, int], Depends(page_to_limit_offset)]
SETTINGS = Annotated[Settings, Depends(get_settings)]
EMAIL_SENDER = Annotated[EmailSender, Depends(get_email_sender)]
JWT_MANAGER = Annotated[JWTManager, Depends(get_jwt_manager)]
ACCESS_TOKEN = Annotated[str, Depends(get_token)]


async def get_current_user(
    db: DATABASE,
    token_data: TOKEN_DATA
) -> "User":
    from crud.accounts import get_user_by_id
    return await get_user_by_id(db=db, user_id=token_data["user_id"], select_group=True)


async def get_moderator_user(user: "User" = Depends(get_current_user)) -> "User":
    from database.models.accounts import UserGroupEnum

    if user.group.name != UserGroupEnum.MODERATOR and user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No required permission")


async def get_admin_user(user: "User" = Depends(get_current_user)) -> "User":
    from database.models.accounts import UserGroupEnum

    if user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No required permission")


CURRENT_USER = Annotated["User", Depends(get_current_user)]
MODERATOR_USER = Annotated["User", Depends(get_moderator_user)]
ADMIN_USER = Annotated["User", Depends(get_admin_user)]
