from decimal import Decimal

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from database.models.movies import Movie


class _OrderItemSchema(BaseModel):
    price: Decimal = Field(validation_alias="price_at_order")
    name: str = Field(validation_alias="movie")

    @field_validator("name", mode="before")
    @classmethod
    def validate_movie_name(cls, movie: Movie):
        return movie.name


class OrderResponseSchema(BaseModel):
    created_at: datetime
    status: str
    total_amount: Decimal
    movies: list[_OrderItemSchema] = Field(validation_alias="order_items")
