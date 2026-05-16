from datetime import timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from database.models import MovieReaction
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
        return description.replace('"', "'")


class MovieDetailResponseSchema(MovieResponseSchema):
    certification: str
    genres: list[str]

    comments: list[dict] = Field(validation_alias="reactions")
    likes: int
    dislikes: int

    @field_validator("comments", mode="before")
    @classmethod
    def validate_comments(cls, comments: list[MovieReaction]) -> list[dict]:
        return [
            {
                "user_id": reaction.user_id,
                "comment": reaction.comment,
                "likes": sum(
                    1
                    for comment_reaction in reaction.comment_answers
                    if comment_reaction.reaction
                ),
                "comment_answers": [
                    {
                        "user_id": answer.user_id,
                        "comment": answer.comment,
                    }
                    for answer in reaction.comment_answers
                    if answer.comment
                ],
            }
            for reaction in comments
            if reaction.comment
        ]

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


class ReactionRequestSchema(BaseModel):
    movie_id: int
    reaction: bool


class CommentRequestSchema(BaseModel):
    movie_id: int
    comment: str


class RawCommentAnswerSchema(BaseModel):
    user_id: int
    movie_id: int


class CommentAnswerRequestSchema(RawCommentAnswerSchema):
    comment: str


class CommentReactionRequestSchema(RawCommentAnswerSchema):
    reaction: bool


class DeleteCommentAnswerRequestSchema(RawCommentAnswerSchema): ...


class DeleteCommentReactionRequestSchema(RawCommentAnswerSchema): ...


class GradeRequestSchema(BaseModel):
    movie_id: int
    grade: int = Field(le=10, ge=1)


class AddToFavoriteRequestSchema(BaseModel):
    movie_id: int


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
