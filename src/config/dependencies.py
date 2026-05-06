from typing import Annotated

from fastapi import Depends, Request, HTTPException, status
from fastapi.params import Query

from config.settings import Settings
from notifications.emails import EmailSender
from security import JWTManager


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
    settings: Settings = Depends(get_settings),
    page: int = Query(default=1, ge=1)
) -> tuple[int, int]:

    limit = settings.DEFAULT_PAGE_SIZE
    offset = limit * (page - 1)

    return limit, offset


def token_data(
    raw_token: str = Depends(get_token),
    jwt_manager: JWTManager = Depends(get_jwt_manager),
) -> dict:
    return jwt_manager.decode_access_token(token=raw_token)


TOKEN_DATA = Annotated[dict, Depends(token_data)]
LIMIT_OFFSET = Annotated[tuple[int, int], Depends(page_to_limit_offset)]
SETTINGS = Annotated[Settings, Depends(get_settings)]
EMAIL_SENDER = Annotated[EmailSender, Depends(get_email_sender)]
JWT_MANAGER = Annotated[JWTManager, Depends(get_jwt_manager)]
ACCESS_TOKEN = Annotated[str, Depends(get_token)]
