from typing import Iterable

from fastapi import HTTPException, status
from asyncpg.exceptions import ForeignKeyViolationError
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Cart, CartItem
from database.models import Movie


async def get_or_create_cart_id(db: AsyncSession, user_id: int) -> int:
    cart_id = await db.scalar(select(Cart.id).where(Cart.user_id == user_id))
    if not cart_id:
        cart_id = await db.scalar(
            insert(Cart).values(user_id=user_id).returning(Cart.id)
        )
    return cart_id

async def add_movie_to_cart_and_create_cart(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    cart_id = await get_or_create_cart_id(db=db, user_id=user_id)
    try:
        db_res = await db.execute(
            insert(CartItem)
            .values(movie_id=movie_id, cart_id=cart_id)
            .on_conflict_do_nothing()
        )
        if db_res.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The movie is already in your cart",
            )
    except IntegrityError as e:
        if isinstance(e.orig.__cause__, ForeignKeyViolationError):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Movie not found"
            )


async def bulk_create_cart_items(db: AsyncSession, user_id: int, movie_ids: set | frozenset) -> None:
    cart_id = await get_or_create_cart_id(db=db, user_id=user_id)
    cart_items = [
        {"movie_id": movie_id, "cart_id": cart_id}
        for movie_id in movie_ids
    ]
    await db.execute(
        insert(CartItem)
        .values(cart_items)
        .on_conflict_do_nothing()
    )


def _get_cart_id_subquery(user_id: int):
    return select(Cart.id).where(Cart.user_id == user_id).scalar_subquery()


async def delete_movie_from_cart_by_movie_id(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    cart_id = _get_cart_id_subquery(user_id=user_id)
    db_res = await db.execute(
        delete(CartItem).where(
            CartItem.movie_id == movie_id, CartItem.cart_id == cart_id
        )
    )
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie in cart not found"
        )


async def delete_all_movies_from_cart_by_user_id(
    db: AsyncSession,
    user_id: int,
) -> None:
    cart_id = _get_cart_id_subquery(user_id=user_id)
    db_res = await db.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="The cart is already empty"
        )


async def get_all_movies_from_cart(db: AsyncSession, user_id: int) -> Iterable[Movie]:
    cart_id = _get_cart_id_subquery(user_id=user_id)
    return await db.scalars(
        select(Movie)
        .join(Movie.cart_items)
        .where(CartItem.cart_id == cart_id)
        .options(selectinload(Movie.genres))
    )
