from sqlalchemy import (
    ForeignKey,
    String,
    CheckConstraint,
    Boolean,
    Integer,
    ForeignKeyConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import Base


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
