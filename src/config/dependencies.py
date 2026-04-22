from fastapi import Depends

from config.settings import Settings
from notifications.emails import EmailSender


def get_settings() -> Settings:
    return Settings()


def get_email_sender(
        settings: Settings = Depends(get_settings),
) -> EmailSender:
    return EmailSender(
        smtp_server=settings.SMTP_SERVER,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD
    )
