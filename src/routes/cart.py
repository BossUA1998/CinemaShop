from fastapi import APIRouter, status, HTTPException

from crud.base_crud import rollback_decorator
from crud.cart import (
    add_movie_to_cart_and_create_cart,
    delete_movie_from_cart_by_movie_id,
    delete_all_movies_from_cart_by_user_id,
    get_all_movies_from_cart,
)
from config.dependencies import TOKEN_DATA, DATABASE, MODERATOR_USER
from schemas.base_schemas import MessageResponseSchema
from schemas.cart import AddToCartRequestSchema, DeleteFromCartRequestSchema
from schemas.movies import MovieInCartResponseSchema

router = APIRouter()


@router.post(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Cart Movies",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def add_movie_to_cart(
    db: DATABASE, token_data: TOKEN_DATA, movie_data: AddToCartRequestSchema
):
    await add_movie_to_cart_and_create_cart(
        db=db,
        movie_id=movie_data.movie_id,
        user_id=token_data["user_id"],
    )
    await db.commit()
    return {"message": "Movie added to cart"}


@router.delete(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Cart Movies",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def delete_movie_from_cart(
    db: DATABASE, token_data: TOKEN_DATA, movie_data: DeleteFromCartRequestSchema
):
    await delete_movie_from_cart_by_movie_id(
        db=db,
        movie_id=movie_data.movie_id,
        user_id=token_data["user_id"],
    )
    await db.commit()
    return {"message": "Movie deleted from cart"}


@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Cart Movies",
    response_model=list[MovieInCartResponseSchema],
)
async def get_all_cart(
    db: DATABASE,
    token_data: TOKEN_DATA,
):
    return await get_all_movies_from_cart(
        db=db,
        user_id=token_data["user_id"],
    )


@router.delete(
    path="/all/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cart Movies",
)
@rollback_decorator()
async def delete_all_movies_from_cart(
    db: DATABASE,
    token_data: TOKEN_DATA,
):
    await delete_all_movies_from_cart_by_user_id(
        db=db,
        user_id=token_data["user_id"],
    )
    await db.commit()


@router.get(
    path="/{user_id}/all/",
    status_code=status.HTTP_200_OK,
    summary="Cart Movies",
    response_model=list[MovieInCartResponseSchema],
    responses={}
)
async def get_user_cart_by_moderator(
    db: DATABASE,
    user: MODERATOR_USER,
    user_id: int
):
    if user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This is your shopping cart, to view it use the current link without specifying the user ID"
        )
    return await get_all_movies_from_cart(
        db=db,
        user_id=user_id,
    )
