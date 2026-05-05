from datetime import timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from database.models.movies import Star, Director


class MovieResponseSchema(BaseModel):
    id: int
    name: str
    year: int
    stars: list[str]
    director: str = Field(validation_alias="directors")
    time: str
    votes: int
    description: str
    price: Decimal
    rating: float = Field(validation_alias="imdb")

    @field_validator("time", mode="before")
    @classmethod
    def validate_time(cls, time_in_minutes: int) -> str:
        return str(timedelta(minutes=time_in_minutes))

    @field_validator("stars", mode="before")
    @classmethod
    def validate_actor(cls, stars: list[Star]) -> list[str]:
        return [star.name for star in stars]

    @field_validator("director", mode="before")
    @classmethod
    def validate_director(cls, director: list[Director]) -> list[str]:
        return director[0].name

    @field_validator("description")
    @classmethod
    def validate_description(cls, description: str) -> str:
        return description.replace("\"", "\'")


class PaginatedMovieResponseSchema(BaseModel):
    next_page: Optional[str]
    previous_page: Optional[str]
    movies: list[MovieResponseSchema]
