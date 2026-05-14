import uuid
from typing import Optional
from uuid import UUID

from decimal import Decimal
from datetime import datetime, date, timezone, timedelta
from enum import auto, StrEnum

from sqlalchemy import Enum, String, Boolean, DateTime, func, ForeignKey, Date, UniqueConstraint, Integer, Float, Uuid, \
    Text, Numeric, Table, Column, CheckConstraint, ForeignKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from database.session import Base
from database.validators import accounts as validators

from security import passwords_manager


# ----------------------------------------------------------------------------------------------------------------------
# --- Account models ---
# ----------------------------------------------------------------------------------------------------------------------

class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MAN = auto()
    WOMAN = auto()


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    name: Mapped[UserGroupEnum] = mapped_column(
        Enum(UserGroupEnum), nullable=False, unique=True
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    _hashed_password: Mapped[str] = mapped_column(
        "hashed_password", String(255), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id", ondelete="RESTRICT"), nullable=False
    )
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel", back_populates="users"
    )

    activation_token: Mapped[Optional["ActivationTokenModel"]] = relationship(
        "ActivationTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    password_reset_token: Mapped[Optional["PasswordResetTokenModel"]] = relationship(
        "PasswordResetTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", cascade="all, delete-orphan"
    )

    reactions: Mapped[list["MovieReaction"]] = relationship(
        "MovieReaction", back_populates="user"
    )
    favorite_movies_by_user: Mapped[list["Movie"]] = relationship(
        "Movie", secondary="favorite_movies"
    )

    @property
    def password(self) -> None:
        raise AttributeError(
            "Password is not a readable attribute. Use a setter to set the password."
        )

    @password.setter
    def password(self, raw_password: str) -> None:
        validators.validate_password_strength(raw_password)
        self._hashed_password = passwords_manager.hash_password(raw_password)

    @validates("email")
    def validate_email(self, key, email: str) -> bool:
        return validators.validate_email(email)

    def verify_password(self, password: str) -> bool:
        return passwords_manager.verify_password(
            raw_password=password, hashed_password=self._hashed_password
        )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    info: Mapped[str] = mapped_column(String(511), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class TokenModel(Base):
    __abstract__ = True

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc) + timedelta(hours=24),
    )


class ActivationTokenModel(TokenModel):
    __tablename__ = "activation_tokens"

    user: Mapped["User"] = relationship("User", back_populates="activation_token")


class PasswordResetTokenModel(TokenModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped["User"] = relationship("User", back_populates="password_reset_token")


class RefreshTokenModel(TokenModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(511), nullable=False, unique=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


# ----------------------------------------------------------------------------------------------------------------------
# --- Cart models ---
# ----------------------------------------------------------------------------------------------------------------------

class Cart(Base):
    __tablename__ = "carts"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )


class CartItem(Base):
    __tablename__ = "cart_items"

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "movie_id"),
    )


# ----------------------------------------------------------------------------------------------------------------------
# --- Movie models ---
# ----------------------------------------------------------------------------------------------------------------------

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
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=MoviesGenres, back_populates="genres"
    )


class Star(Base):
    __tablename__ = "stars"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=MovieStars, back_populates="stars"
    )


class Director(Base):
    __tablename__ = "directors"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary=MoviesDirectors, back_populates="directors"
    )


class Certification(Base):
    __tablename__ = "certifications"

    name: Mapped[str] = mapped_column(String(31), nullable=False, unique=True)
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", back_populates="certification"
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

    genres: Mapped[list["Genre"]] = relationship(
        "Genre", secondary=MoviesGenres, back_populates="movies"
    )

    directors: Mapped[list["Director"]] = relationship(
        "Director", secondary=MoviesDirectors, back_populates="movies"
    )

    stars: Mapped[list["Star"]] = relationship(
        "Star", secondary=MovieStars, back_populates="movies"
    )

    reactions: Mapped[list["MovieReaction"]] = relationship("MovieReaction")

    favorite_movies: Mapped[list["FavoriteMovie"]] = relationship("FavoriteMovie", overlaps="favorite_movies_by_user")
    cart_items: Mapped[list[CartItem]] = relationship("CartItem")

    __table_args__ = (UniqueConstraint("name", "year", "time"),)


# ----------------------------------------------------------------------------------------------------------------------
# --- Order models ---
# ----------------------------------------------------------------------------------------------------------------------

class OrderStatus(StrEnum):
    pending = auto()
    paid = auto()
    canceled = auto()


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), server_default=OrderStatus.pending)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False)
    price_at_order: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    movie: Mapped["Movie"] = relationship("Movie")
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")


# ----------------------------------------------------------------------------------------------------------------------
# --- Reaction models ---
# ----------------------------------------------------------------------------------------------------------------------

class MovieReaction(Base):
    __tablename__ = "movie_reactions"

    id = None
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )

    reaction: Mapped[bool] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str] = mapped_column(String(1023), nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="reactions")
    comment_answers: Mapped[list["CommentAnswer"]] = relationship(
        "CommentAnswer", back_populates="reaction_movie"
    )

    __table_args__ = (
        CheckConstraint(
            "reaction IS NOT NULL OR comment IS NOT NULL OR grade IS NOT NULL",
            name="ck_reaction_or_comment_or_grade",
        ),
        CheckConstraint("grade BETWEEN 1 AND 10", name="ck_grade_range"),
    )


class FavoriteMovie(Base):
    __tablename__ = "favorite_movies"

    id = None
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )


class CommentAnswer(Base):
    __tablename__ = "comment_answers"

    id = None
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    movie_reaction_user_id: Mapped[int] = mapped_column(primary_key=True)
    movie_reaction_movie_id: Mapped[int] = mapped_column(primary_key=True)

    comment: Mapped[str] = mapped_column(String(1023), nullable=True)
    reaction: Mapped[bool] = mapped_column(Boolean, nullable=True)

    user: Mapped["User"] = relationship("User")
    reaction_movie: Mapped["MovieReaction"] = relationship(
        "MovieReaction", back_populates="comment_answers"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["movie_reaction_user_id", "movie_reaction_movie_id"],
            ["movie_reactions.user_id", "movie_reactions.movie_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "comment IS NOT NULL OR reaction IS NOT NULL", name="ck_reaction_or_comment"
        ),
    )
