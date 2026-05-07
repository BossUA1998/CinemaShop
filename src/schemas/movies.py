from collections import Counter
from datetime import timedelta
from decimal import Decimal
from functools import cached_property
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field

from database.models import User, MovieReaction
from database.models.movies import Star, Director, Certification, Genre, Movie


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


class _CommentSchema(BaseModel):
    user_email: str = Field(validation_alias="user")
    comment: str

    @field_validator("user_email", mode="before")
    @classmethod
    def validate_user_email(cls, user: User) -> str:
        email, _, email_host = user.email.partition("@")
        return f"{email[0]}{"*" * len(email[1:-1])}{email[-1]}@{email_host}"


class MovieDetailResponseSchema(MovieResponseSchema):
    certification: str
    genres: list[str]
    comments: list[_CommentSchema] = Field(validation_alias="reactions")
    likes: int
    dislikes: int

    @field_validator("certification", mode="before")
    @classmethod
    def validate_certification(cls, certification: Certification) -> str:
        return certification.name

    @field_validator("genres", mode="before")
    @classmethod
    def validate_genres(cls, genres: list[Genre]) -> list[str]:
        return [genre.name for genre in genres]


class PaginatedMovieResponseSchema(BaseModel):
    next_page: Optional[str]
    previous_page: Optional[str]
    movies: list[MovieResponseSchema]


class DeleteReactionOrCommentRequestSchema(BaseModel):
    movie_id: int


class ReactionRequestSchema(DeleteReactionOrCommentRequestSchema):
    reaction: bool


class CommentRequestSchema(DeleteReactionOrCommentRequestSchema):
    comment: str


class GradeRequestSchema(DeleteReactionOrCommentRequestSchema):
    grade: int = Field(le=10, ge=1)


class AddToFavoriteRequestSchema(DeleteReactionOrCommentRequestSchema):
    ...


class GenresResponseSchema(BaseModel):
    genre: str
    movies: int


class GenreDetailResponseSchema(BaseModel):
    genre: str = Field(validation_alias="name")
    movies: list[str]

    @field_validator("movies", mode="before")
    @classmethod
    def validate_movies(cls, movies: list[Movie]) -> list[str]:
        return [movie.name for movie in movies]
