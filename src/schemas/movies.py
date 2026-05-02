from datetime import timedelta
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class MovieResponseSchema(BaseModel):
    name: str
    year: int
    genre: str
    time: int
    votes: int
    description: str
    price: Decimal

    rating: str = Field(validation_alias="imdb")

    @field_validator("time")
    @classmethod
    def validate_time(cls, time_in_minutes: int):
        return timedelta(minutes=time_in_minutes)
