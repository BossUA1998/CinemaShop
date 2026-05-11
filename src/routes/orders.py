from fastapi import APIRouter, status

from crud.base_crud import rollback_decorator
from crud.orders import create_orders_by_user_id, get_order
from schemas.base_schemas import MessageResponseSchema
from database import DATABASE
from config.dependencies import TOKEN_DATA
from schemas.orders import OrderResponseSchema

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
    response_model=OrderResponseSchema,
)
async def get_orders(
    db: DATABASE,
    token_data: TOKEN_DATA,
):
    return await get_order(db=db, user_id=token_data["user_id"])
