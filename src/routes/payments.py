import stripe
from fastapi import APIRouter, status, Request, HTTPException, BackgroundTasks
from config.dependencies import SETTINGS, TOKEN_DATA, DATABASE
from config.settings import Settings
from crud.base_crud import rollback_decorator
from crud.orders import get_order
from crud.payments import create_payment
from database.models import OrderStatus, Movie, OrderItem
from schemas.payments import CreatePaymentRequestSchema

router = APIRouter()


async def _create_payment_session(
    settings: "Settings",
    movies: list[Movie],
    metadata: dict
):
    line_items = [
        {
            "price_data": {
                "currency": "USD",
                "product_data": {
                    "name": movie.name,
                    "description": movie.description,
                },
                "unit_amount": int(movie.price * 100),
            },
            "quantity": 1,
        }
        for movie in movies
    ]
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_intent_data={"metadata": metadata},
        line_items=line_items,
        metadata=metadata,
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
    )
    return session.url


@router.post(
    path="/webhook/",
    status_code=status.HTTP_200_OK,
    summary="Payments Webhook",
)
async def payments_webhook(request: Request, settings: SETTINGS):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
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
    payment_data: CreatePaymentRequestSchema,
    settings: SETTINGS,
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

    payment_id = await create_payment(
        db=db,
        user_id=user_id,
        order=order
    )

    payment_url = await _create_payment_session(
        movies=(
            movie
            for movie in (
                order_item.movie
                for order_item in order.order_items
            )
        ),
        settings=settings,
        metadata={"payment_id": payment_id}
    )
    await db.commit()
    return {"payment": payment_url}
