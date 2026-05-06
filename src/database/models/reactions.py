from sqlalchemy import ForeignKey, String, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from database.models import Base


class MovieReaction(Base):
    __tablename__ = "movie_reactions"

    id = None
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True)
    reaction: Mapped[bool] = mapped_column(Boolean, nullable=True)
    comment: Mapped[str] = mapped_column(String(1023), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "reaction IS NOT NULL OR comment IS NOT NULL",
            name="ck_reaction_or_comment"
        ),
    )
