from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.cart import Cart, CartItem


async def add_movie_to_cart_and_create_cart(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    cart_id = await db.scalar(
        select(Cart.id)
        .where(
            Cart.user_id == user_id
        )
    )
    if not cart_id:
        cart_id = await db.scalar(
            insert(Cart)
            .values(
                user_id=user_id
            )
            .returning(Cart.id)
        )
    db_res = await db.execute(
        insert(CartItem)
        .values(
            movie_id=movie_id,
            cart_id=cart_id
        )
        .on_conflict_do_nothing()
    )
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The movie is already in your cart"
        )


async def delete_movie_from_cart_by_movie_id(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
) -> None:
    cart_id = (
        select(Cart.id)
        .where(
            Cart.user_id == user_id
        )
        .scalar_subquery()
    )
    db_res = await db.execute(
        delete(CartItem)
        .where(
            CartItem.movie_id == movie_id,
            CartItem.cart_id == cart_id
        )
    )
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie in cart not found"
        )
