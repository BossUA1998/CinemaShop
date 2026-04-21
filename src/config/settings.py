from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    SECRET_KEY_ACCESS: str = os.getenv("SECRET_KEY_ACCESS", os.urandom(32).hex())
    SECRET_KEY_REFRESH: str = os.getenv("SECRET_KEY_REFRESH", os.urandom(32).hex())
    JWT_SIGNING_ALGORITHM: str = os.getenv("JWT_SIGNING_ALGORITHM", "HS256")

    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "movies_db")
    POSTGRES_DB_PORT: str = os.getenv("POSTGRES_DB_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "1qazcde3")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres_cinema_shop")
