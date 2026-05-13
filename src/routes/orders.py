from fastapi import APIRouter, status

from crud.base_crud import rollback_decorator
from crud.orders import create_orders_by_user_id, get_orders
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
    summary="Cart Orders",
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
    summary="Cart Orders",
    response_model=list[OrderForModeratorsSchema],
    responses={}
)
async def get_all_orders_by_moderator_user(
    db: DATABASE,
    user: MODERATOR_USER, # noqa
):
    return await get_orders(db=db)
