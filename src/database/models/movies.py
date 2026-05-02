import uuid
from decimal import Decimal
from typing import List
from uuid import UUID
from sqlalchemy import (
    String,
    Integer,
    Float,
    Uuid,
    Text,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Table,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base

MoviesGenres = Table(
    "movies_genres",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "genre_id",
        Base.metadata,
        ForeignKey("genres.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)

MoviesDirectors = Table(
    "movie_directors",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "director_id",
        ForeignKey("directors.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


MovieStars = Table(
    "movie_stars",
    Base.metadata,
    Column(
        "movie_id",
        ForeignKey("movies.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "star_id",
        ForeignKey("stars.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
)


class Genre(Base):
    __tablename__ = "genres"

    name: Mapped[str] = mapped_column(String(63), nullable=False, unique=True)
    movies: Mapped[List["Movie"]] = relationship(
        "Movie",
        secondary=MoviesGenres,
        back_populates="genres"
    )


class Star(Base):
    __tablename__ = "stars"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    movies: Mapped[List["Movie"]] = relationship(
        "Movie",
        secondary=MovieStars,
        back_populates="stars"
    )


class Director(Base):
    __tablename__ = "directors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    movies: Mapped[List["Movie"]] = relationship(
        "Movie",
        secondary=MoviesDirectors,
        back_populates="directors"
    )


class Certification(Base):
    __tablename__ = "certifications"

    name: Mapped[str] = mapped_column(String(31), nullable=False, unique=True)
    movies: Mapped[List["Movie"]] = relationship(
        "Movie",
        back_populates="certification"
    )


class Movie(Base):
    __tablename__ = "movies"

    uuid: Mapped[UUID] = mapped_column(Uuid, unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float] = mapped_column(Float, nullable=True)
    gross: Mapped[float] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id", ondelete="RESTRICT"), nullable=True
    )
    certification: Mapped["Certification"] = relationship(
        "Certification", back_populates="movies"
    )

    __table_args__ = (UniqueConstraint("name", "year", "time"),)

    genres: Mapped[List["Genre"]] = relationship(
        "Genre", secondary=MoviesGenres, back_populates="movies"
    )

    directors: Mapped[List["Director"]] = relationship(
        "Director", secondary=MoviesDirectors, back_populates="movies"
    )

    stars: Mapped[List["Star"]] = relationship(
        "Star", secondary=MovieStars, back_populates="movies"
    )
