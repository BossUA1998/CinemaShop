import secrets

from typing import Annotated

from fastapi import APIRouter, status, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from notifications.emails import EmailSender

from config.dependencies import get_email_sender

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    ActivationRequestSchema
from crud.accounts import create_new_user, create_activation_token, get_user_by_activation_token

router = APIRouter()

DATABASE = Annotated[AsyncSession, Depends(get_db)]
EMAIL_SENDER = Annotated[EmailSender, Depends(get_email_sender)]


@router.post(
    path="/register/",
    response_model=UserRegistrationResponseSchema,
    summary="User Registration",
    description="Register a new user with an email and password",
    status_code=status.HTTP_201_CREATED,
    responses={}
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
            activation_link=str(request.url_for("activate_user"))
        )
        await db.commit()
        return user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")


@router.post(
    path="/activate/",
    response_model=MessageResponseSchema,
    summary="User Activate",
    status_code=status.HTTP_200_OK,
    responses={}
)
async def activate_user(
        activation_data: Annotated[ActivationRequestSchema, Depends(ActivationRequestSchema.as_form)],
        db: DATABASE,
        email_sender: EMAIL_SENDER,
        background_tasks: BackgroundTasks
):
    user = await get_user_by_activation_token(db=db, token=activation_data.token)
    user.is_active = True
    background_tasks.add_task(
        email_sender.send_activation_complete_email,
        email=user.email,
    )
    await db.commit()
    return {"message": "User activated"}
