from decimal import Decimal

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from database.models import Movie


class _OrderItemSchema(BaseModel):
    movie_id: int = Field(validation_alias="movie")
    price: Decimal = Field(validation_alias="price_at_order")
    name: str = Field(validation_alias="movie")

    @field_validator("movie_id", mode="before")
    @classmethod
    def validate_movie_id(cls, movie: Movie) -> int:
        return movie.id

    @field_validator("name", mode="before")
    @classmethod
    def validate_movie_name(cls, movie: Movie):
        return movie.name


class OrderResponseSchema(BaseModel):
    id: int
    created_at: datetime
    status: str
    total_amount: Decimal
    movies: list[_OrderItemSchema] = Field(validation_alias="order_items")


class OrderForModeratorsSchema(OrderResponseSchema):
    user_id: int
