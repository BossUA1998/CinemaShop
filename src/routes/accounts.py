import secrets
from datetime import datetime, timezone

from typing import Annotated

from fastapi import APIRouter, status, BackgroundTasks, Depends, HTTPException, Request, Form
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from notifications.emails import EmailSender

from config.dependencies import get_email_sender

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    ActivationRequestSchema
from crud.accounts import create_new_user, create_activation_token, get_user_by_activation_token, \
    delete_all_activation_tokens, get_activation_token, get_user_by_email
from celery_worker.tasks import delete_activation_token
router = APIRouter()

DATABASE = Annotated[AsyncSession, Depends(get_db)]
EMAIL_SENDER = Annotated[EmailSender, Depends(get_email_sender)]


@router.post(
    path="/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email and password",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "User already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "This email address is already registered"
                    }
                }
            }
        },
    }
)
async def register_user(
        request: Request,
        user_data: UserRegistrationRequestSchema,
        background_tasks: BackgroundTasks,
        db: DATABASE,
        email_sender: EMAIL_SENDER
):
    try:
        user = await create_new_user(db=db, user_data=user_data)

        token = secrets.token_hex()
        await create_activation_token(db=db, token=token, user=user)

        background_tasks.add_task(
            email_sender.send_activation_email,
            email=user.email,
            token=token,
            activation_link=str(request.url_for("activate_user")),
            new_activation_link=str(request.url_for("new_activation_token"))
        )
        await db.commit()
        return user

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This email address is already registered")


@router.post(
    path="/activate/",
    response_model=MessageResponseSchema,
    summary="User Activate",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "There is no user with this token",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Token not found"
                    }
                }
            }
        }
    }
)
async def activate_user(
        activation_data: Annotated[ActivationRequestSchema, Depends(ActivationRequestSchema.as_form)],
        db: DATABASE,
        email_sender: EMAIL_SENDER,
        background_tasks: BackgroundTasks
):
    try:
        token = await get_activation_token(db=db, token=activation_data.token)

        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
            )

        if token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This token has expired")

        user = await get_user_by_activation_token(db=db, token=activation_data.token)
        user.is_active = True

        await delete_all_activation_tokens(db=db, email=user.email)

        background_tasks.add_task(
            email_sender.send_activation_complete_email,
            email=user.email,
        )
        await db.commit()
        return {"message": "Account activated"}
    except Exception:
        await db.rollback()
        raise


@router.post(
    path="/new-activate/",
    response_model=MessageResponseSchema,
    summary="New Activation Token",
    status_code=status.HTTP_201_CREATED,
    responses={}
)
async def new_activation_token(
        request: Request,
        db: DATABASE,
        email_sender: EMAIL_SENDER,
        background_tasks: BackgroundTasks,
        email: str = Form(...)
):
    try:
        user = await get_user_by_email(db=db, email=email)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

        if user.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already active")

        await delete_all_activation_tokens(db=db, email=email)
        token = secrets.token_hex()
        await create_activation_token(db=db, token=token, user=user)
        background_tasks.add_task(
            email_sender.send_activation_email,
            email=email,
            token=token,
            activation_link=str(request.url_for("activate_user")),
            new_activation_link=str(request.url_for("new_activation_token"))
        )
        await db.commit()

        delete_activation_token.apply_async(
            args=[token], countdown=25 # day
        )

        return {"message": "If the email is correct, the message has been sent"}
    except Exception:
        await db.rollback()
        raise
