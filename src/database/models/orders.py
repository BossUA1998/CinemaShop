from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from sqlalchemy import Numeric, ForeignKey, Enum, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models import Base


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
