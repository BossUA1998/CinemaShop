import stripe
from fastapi import APIRouter, status, Request, HTTPException
from config.dependencies import SETTINGS, TOKEN_DATA, DATABASE
from crud.base_crud import rollback_decorator
from crud.orders import get_order
from crud.payments import create_payment
from database.models import OrderStatus
from schemas.payments import CreatePaymentRequestSchema

router = APIRouter()


@router.post(
    path="/webhook/",
    status_code=status.HTTP_200_OK,
    summary="Payments Webhook",
)
async def payments_webhook(request: Request, settings: SETTINGS):
    client = settings.STRIPE_CLIENT
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = client.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_KEY
        )
    except stripe.error.SignatureVerificationError:
        raise

    match event["type"]:
        case "checkout.session.completed":
            ...
        case "charge.succeeded":
            ...
            # TODO implement to send receipt on email
        case "checkout.session.expired":
            ...

@router.post(
    path="/create/",
    status_code=status.HTTP_201_CREATED,
    summary="Payments Session",
)
@rollback_decorator()
async def payments_session(
    db: DATABASE,
    token_data: TOKEN_DATA,
    payment_data: CreatePaymentRequestSchema
):
    user_id = token_data["user_id"]
    order_id = payment_data.order_id

    order = await get_order(
        db=db,
        order_id=order_id,
        select_movies=True
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not your order"
        )

    if order.status == OrderStatus.paid or order.status == OrderStatus.canceled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This order cannot be paid for"
        )

    await create_payment(
        db=db,
        user_id=user_id,
        order=order
    )

    await db.commit()

