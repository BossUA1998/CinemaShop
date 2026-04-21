from datetime import datetime, date, timezone, timedelta
from enum import auto, StrEnum
from typing import List

from sqlalchemy import Enum, String, Boolean, DateTime, func, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import Base


class UserGroupEnum(StrEnum):
    USER = auto()
    MODERATOR = auto()
    ADMIN = auto()


class GenderEnum(StrEnum):
    MAN = auto()
    WOMAN = auto()


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    name: Mapped[UserGroupEnum] = mapped_column(Enum(UserGroupEnum), nullable=False, unique=True)
    users: Mapped[List["User"]] = relationship("User", back_populates="group")


class User(Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    _hashed_password: Mapped[str] = mapped_column("hashed_password", String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("user_groups.id", ondelete="RESTRICT"), nullable=False)
    group: Mapped["UserGroupModel"] = relationship("UserGroupModel", back_populates="users")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    info: Mapped[str] = mapped_column(String(511), nullable=False)


class TokenModel(Base):
    __abstract__ = True

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc) + timedelta(hours=24)
    )


class ActivationToken(TokenModel):
    __tablename__ = "activation_tokens"

    user: Mapped["User"] = relationship("User", back_populates="activation_token")


class PasswordResetToken(TokenModel):
    __tablename__ = "password_reset_tokens"

    user: Mapped["User"] = relationship("User", back_populates="password_reset_token")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(511), nullable=False, unique=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_token")
