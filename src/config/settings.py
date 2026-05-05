from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    PATH_TO_EMAIL_TEMPLATES: str = str(BASE_DIR / "notifications" / "templates")
    PATH_TO_CSV: str = str(BASE_DIR / "database" / "datasets" / "imdb_movies.csv")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete.html"

    SECRET_KEY_ACCESS: str = os.urandom(32).hex()
    SECRET_KEY_REFRESH: str = os.urandom(32).hex()
    ACCESS_TOKEN_LIFETIME: int = 30  # Minutes
    REFRESH_TOKEN_LIFETIME: int = 7  # Days
    JWT_SIGNING_ALGORITHM: str = "HS256"

    POSTGRES_DB: str = "movies_db"
    POSTGRES_DB_PORT: str = "5432"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "1qazcde3"
    POSTGRES_HOST: str = "postgres_cinema_shop"

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: str = "587"
    SMTP_USER: str = "test@gmail.com"
    SMTP_PASSWORD: str = "1qazcde3"

    DEFAULT_PAGE_SIZE: int = 100

    @field_validator("SMTP_PASSWORD")
    @classmethod
    def clean_smtp_password(cls, value: str) -> str:
        return value.replace("|", " ")
