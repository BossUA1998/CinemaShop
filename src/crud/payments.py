from fastapi import HTTPException, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, Payment, PaymentItem


async def create_payment(db: AsyncSession, user_id: int, order: Order) -> None:
    movies = [
        order_item.movie for order_item in order.order_items
    ]

    total_amount = sum(
        movie.price
        for movie in movies
    )

    payment_id = await db.scalar(
        insert(Payment)
        .values(
            user_id=user_id,
            order_id=order.id,
            amount=total_amount
        )
        .on_conflict_do_nothing()
        .returning(Payment.id)
    )
    if not payment_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Error creating payment"
        )

    raw_payment_items = [
        {
            "payment_id": payment_id,
            "order_item_id": order_item.id,
            "price_at_payment": movie.price
        }
        for order_item, movie in zip(order.order_items, movies)
    ]

    await db.execute(
        insert(PaymentItem)
        .values(raw_payment_items)
    )
