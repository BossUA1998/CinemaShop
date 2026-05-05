from enum import StrEnum, auto

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column

from database.models import Base


class ReactionType(StrEnum):
    like = auto()
    dislike = auto()


class MovieReaction(Base):
    __tablename__ = "movie_reactions"

    id = None

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    reaction: Mapped[ReactionType] = mapped_column(Enum(ReactionType), nullable=False)
