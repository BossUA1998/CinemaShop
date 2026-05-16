import os
import stripe
from typing import Optional
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).parent.parent

    PATH_TO_EMAIL_TEMPLATES: str = str(BASE_DIR / "notifications" / "templates")
    PATH_TO_CSV: str = str(BASE_DIR / "database" / "datasets" / "imdb_movies.csv")
    ACTIVATION_EMAIL_TEMPLATE_NAME: str = "activation_request.html"
    ACTIVATION_COMPLETE_EMAIL_TEMPLATE_NAME: str = "activation_complete.html"
    PASSWORD_RESET_TEMPLATE_NAME: str = "password_reset_request.html"
    PASSWORD_RESET_COMPLETE_TEMPLATE_NAME: str = "password_reset_complete.html"
    COMMENT_ANSWER_TEMPLATE_NAME: str = "comment_answer.html"
    COMMENT_REACTION_TEMPLATE_NAME: str = "comment_reaction.html"
    IMPOSSIBLE_DELETE_MOVIE_TEMPLATE_NAME: str = "impossible_delete_movie.html"

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
    DATABASE_URL: Optional[str] = None

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: str = "587"
    SMTP_USER: str = "test@gmail.com"
    SMTP_PASSWORD: str = "1qazcde3"

    DEFAULT_PAGE_SIZE: int = 100

    STRIPE_PRIVATE_KEY: str = ""
    STRIPE_WEBHOOK_KEY: str = ""
    STRIPE_SUCCESS_URL: str = ""
    STRIPE_CANCEL_URL: str = ""

    @model_validator(mode="after")
    def set_stripe_api_key(self):
        self.DATABASE_URL = (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

        stripe.api_key = self.STRIPE_PRIVATE_KEY
        return self

    @field_validator("SMTP_PASSWORD")
    @classmethod
    def clean_smtp_password(cls, value: str) -> str:
        return value.replace("|", " ")
