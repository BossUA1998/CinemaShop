from datetime import datetime
from typing import Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, exists, delete, cast, Date
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Order, OrderItem, OrderStatus


async def create_orders_by_user_id(db: AsyncSession, user_id: int) -> None:
    from crud.cart import get_all_movies_from_cart, delete_all_movies_from_cart_by_user_id

    movies_from_cart = await get_all_movies_from_cart(db=db, user_id=user_id)
    movies_from_cart_list = movies_from_cart.all()

    if not movies_from_cart_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Your cart is empty",
        )

    total_amount = sum(movie.price for movie in movies_from_cart_list)
    order_id = await db.scalar(
        insert(Order).values(user_id=user_id, total_amount=total_amount).returning(Order.id)
    )

    purchased_films = await db.scalars(
        select(OrderItem.movie_id)
        .join(OrderItem.order)
        .where(Order.user_id == user_id)
    )

    movies_id_name_dictionary = {
        movie.id: movie.name
        for movie in movies_from_cart_list
    }
    movies_duplicates = frozenset(purchased_films) & frozenset(movie.id for movie in movies_from_cart_list)
    if movies_duplicates:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The films "
                   f"[{", ".join(f"'{movies_id_name_dictionary[movie_id]}'" for movie_id in movies_duplicates)}] "
                   f"have already been purchased",
        )

    raw_order_items = [
        {
            "order_id": order_id,
            "movie_id": movie.id,
            "price_at_order": movie.price,
        }
        for movie in movies_from_cart_list
    ]

    await db.execute(
        insert(OrderItem)
        .values(raw_order_items)
    )
    await delete_all_movies_from_cart_by_user_id(db=db, user_id=user_id)


async def _get_is_purchased_movie(db: AsyncSession, movie_id: int) -> bool:
    return await db.scalar(
        select(exists().where(OrderItem.movie_id == movie_id))
    )


async def get_order(db: AsyncSession, order_id: int, select_movies: bool = False) -> Optional[Order]:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
    )
    if select_movies:
        stmt = stmt.options(
            selectinload(Order.order_items).selectinload(OrderItem.movie)
        )
    else:
        stmt = stmt.options(
            selectinload(Order.order_items)
        )
    return await db.scalar(stmt)


async def get_orders(
    db: AsyncSession,
    user_id: Optional[int] = None,
    created_at: Optional[datetime] = None,
    status: Optional[OrderStatus] = None
)-> Iterable[Order]:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.order_items).selectinload(OrderItem.movie)
        )
    )
    if user_id:
        stmt = stmt.where(Order.user_id == user_id)
    if created_at:
        stmt = stmt.where(
            cast(Order.created_at, Date) == created_at.date()
        )
    if status:
        stmt = stmt.where(Order.status == status)
    return await db.scalars(stmt)


async def delete_order_by_id(db: AsyncSession, order_id: int, user_id: int) -> bool:
    db_res = await db.execute(
        delete(Order)
        .where(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.status == OrderStatus.pending
        )
    )
    return db_res.rowcount == 1
