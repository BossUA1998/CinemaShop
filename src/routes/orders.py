from datetime import datetime

from fastapi import APIRouter, status, HTTPException
from fastapi.params import Query

from crud.base_crud import rollback_decorator
from crud.cart import bulk_create_cart_items
from crud.orders import create_orders_by_user_id, get_orders, get_order, delete_order_by_id
from database.models import OrderStatus
from schemas.base_schemas import MessageResponseSchema
from config.dependencies import TOKEN_DATA, DATABASE, MODERATOR_USER
from schemas.orders import OrderResponseSchema, OrderForModeratorsSchema

router = APIRouter()


@router.post(
    path="/create/",
    status_code=status.HTTP_201_CREATED,
    summary="Cart Order",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def create_order(
    db: DATABASE,
    token_data: TOKEN_DATA,
):
    await create_orders_by_user_id(db=db, user_id=token_data["user_id"])
    await db.commit()
    return {"message": "Order created"}


@router.get(
    path="/",
    status_code=status.HTTP_200_OK,
    summary="Get User Orders",
    response_model=list[OrderResponseSchema],
)
async def get_user_orders(
    db: DATABASE,
    token_data: TOKEN_DATA,
):
    return await get_orders(db=db, user_id=token_data["user_id"])


@router.get(
    path="/all/",
    status_code=status.HTTP_200_OK,
    summary="Get Orders",
    response_model=list[OrderForModeratorsSchema],
    responses={}
)
async def get_all_orders_by_moderator_user(
    db: DATABASE,
    user: MODERATOR_USER, # noqa

    # query
    user_id: int = Query(default=None, ge=1),
    created_at: datetime = Query(default=None),
    status: OrderStatus = Query(default=None),
):
    return await get_orders(db=db, user_id=user_id, created_at=created_at, status=status)


@router.delete(
    path="/{order_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Order",
)
@rollback_decorator()
async def delete_order(
    db: DATABASE,
    order_id: int,
    token_data: TOKEN_DATA,
):
    user_id = token_data["user_id"]

    order = await get_order(db=db, order_id=order_id)
    order_movie_ids = frozenset(order_item.movie_id for order_item in order.order_items)

    await bulk_create_cart_items(db=db, user_id=user_id, movie_ids=order_movie_ids)

    is_deleted = await delete_order_by_id(db=db, user_id=user_id, order_id=order_id)
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cancellable order not found",
        )

    await db.commit()
