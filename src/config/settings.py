from pathlib import Path

from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    BASE_DIR = Path(__file__).parent.parent

    PATH_TO_EMAIL_TEMPLATES: str = str(BASE_DIR / "notifications" / "templates")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete.html"

    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", os.urandom(32).hex())
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", os.urandom(32).hex())
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")

    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "movies_db")
    POSTGRES_DB_PORT: str = os.getenv("POSTGRES_DB_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1qazcde3")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres_cinema_shop")

    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: str = os.getenv("SMTP_PORT", "587")
    SMTP_USER: str = os.getenv("SMTP_USER", "test@localhost.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "1qazcde3").replace("|", " ")
