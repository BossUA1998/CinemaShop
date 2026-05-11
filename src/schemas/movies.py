from datetime import timedelta
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ValidationError

from database.models import MovieReaction
from database.models.movies import Star, Director, Certification, Genre, Movie

from schemas.base_schemas import _RawSchemaWithMovieId


class _RawMovieResponseSchema(BaseModel):
    name: str
    price: Decimal
    year: int


class MovieInCartResponseSchema(_RawMovieResponseSchema):
    genres: list[str]

    @field_validator("genres", mode="before")
    @classmethod
    def validate_genres(cls, genres: list[Genre]) -> list[str]:
        return [genre.name for genre in genres]


class MovieResponseSchema(_RawMovieResponseSchema):
    id: int
    time: str
    stars: list[str]
    votes: int
    description: str
    rating: float = Field(validation_alias="imdb")
    director: str = Field(validation_alias="directors")

    @field_validator("time", mode="before")
    @classmethod
    def validate_time(cls, time_in_minutes: int) -> str:
        return str(timedelta(minutes=time_in_minutes))

    @field_validator("description")
    @classmethod
    def validate_description(cls, description: str) -> str:
        return description.replace('"', "'")

    @field_validator("stars", mode="before")
    @classmethod
    def validate_actor(cls, stars: list[Star]) -> list[str]:
        return [star.name for star in stars]

    @field_validator("director", mode="before")
    @classmethod
    def validate_director(cls, director: list[Director]) -> list[str]:
        return director[0].name


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


class UpdateMovieRequestSchema(BaseModel):
    name: str = None
    year: int = None
    time: int = None
    imdb: float = None
    votes: int = None
    meta_score: int = None
    gross: int = None
    description: str = None
    price: Decimal = None


    @field_validator("year")
    @classmethod
    def validate_year(cls, year: int) -> int:
        if len(str(year)) > 4:
            raise ValidationError("Year must be less than 4 symbols")
        return year


class PaginatedMovieResponseSchema(BaseModel):
    next_page: Optional[str]
    previous_page: Optional[str]
    movies: list[MovieResponseSchema]


class ReactionRequestSchema(_RawSchemaWithMovieId):
    reaction: bool


class CommentRequestSchema(_RawSchemaWithMovieId):
    comment: str


class GradeRequestSchema(_RawSchemaWithMovieId):
    grade: int = Field(le=10, ge=1)


class _RawCommentAnswerSchema(_RawSchemaWithMovieId):
    user_id: int


class CommentAnswerRequestSchema(_RawCommentAnswerSchema):
    comment: str


class CommentReactionRequestSchema(_RawCommentAnswerSchema):
    reaction: bool


class DeleteReactionRequestSchema(_RawSchemaWithMovieId): ...


class DeleteCommentRequestSchema(_RawSchemaWithMovieId): ...


class DeleteGradeRequestSchema(_RawSchemaWithMovieId): ...


class DeleteCommentAnswerRequestSchema(_RawCommentAnswerSchema): ...


class DeleteCommentReactionRequestSchema(_RawCommentAnswerSchema): ...


class AddToFavoriteRequestSchema(_RawSchemaWithMovieId): ...


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
