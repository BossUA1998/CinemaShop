from fastapi import Depends

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
        password_complete_email_template_name=settings.PASSWORD_RESET_COMPLETE_TEMPLATE_NAME
    )


def get_jwt_manager(settings: Settings = Depends(get_settings)):
    return JWTManager(
        access_secret_key=settings.SECRET_KEY_ACCESS,
        refresh_secret_key=settings.SECRET_KEY_REFRESH,
        algorithm=settings.JWT_SIGNING_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_LIFETIME,
        refresh_token_expire_days=settings.REFRESH_TOKEN_LIFETIME
    )
