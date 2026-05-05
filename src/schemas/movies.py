from datetime import timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from database.models.movies import Genre


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    year: int
    genres: list[str]
    time: str
    votes: int
    description: str
    price: Decimal
    rating: float = Field(validation_alias="imdb")

    @field_validator("time", mode="before")
    @classmethod
    def validate_time(cls, time_in_minutes: int) -> str:
        return str(timedelta(minutes=time_in_minutes))

    @field_validator("genres", mode="before")
    @classmethod
    def validate_genre(cls, genres: list[Genre]) -> list[str]:
        return [genre.name for genre in genres]

    @field_validator("description")
    @classmethod
    def validate_description(cls, description: str) -> str:
        return description.replace("\"", "\'")
