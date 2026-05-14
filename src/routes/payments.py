import stripe
from fastapi import APIRouter, status, Request
from config.dependencies import SETTINGS

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