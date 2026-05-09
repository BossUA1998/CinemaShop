from fastapi import APIRouter, status

from crud.base_crud import rollback_decorator
from crud.cart import add_movie_to_cart_and_create_cart, delete_movie_from_cart_by_movie_id
from database import DATABASE
from config.dependencies import TOKEN_DATA
from schemas.base_schemas import MessageResponseSchema
from schemas.cart import AddToCartRequestSchema

router = APIRouter()


@router.post(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Cart Movies",
    response_model=MessageResponseSchema,
    responses={}
)
@rollback_decorator()
async def add_movie_to_cart(
    db: DATABASE,
    token_data: TOKEN_DATA,
    movie_data: AddToCartRequestSchema
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
    responses={}
)
@rollback_decorator()
async def delete_movie_from_cart(
    db: DATABASE,
    token_data: TOKEN_DATA,
    movie_data: AddToCartRequestSchema
):
    await delete_movie_from_cart_by_movie_id(
        db=db,
        movie_id=movie_data.movie_id,
        user_id=token_data["user_id"],
    )
    await db.commit()
    return {"message": "Movie deleted from cart"}
