import secrets
from calendar import error
from datetime import datetime, timezone

from typing import Annotated

from fastapi import APIRouter, status, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from notifications.emails import EmailSender

from config.dependencies import get_email_sender, get_jwt_manager, get_token

from schemas.accounts import UserRegistrationResponseSchema, UserRegistrationRequestSchema, MessageResponseSchema, \
    ActivationRequestSchema, NewActivationRequestSchema, UserLoginResponseSchema, UserLoginRequestSchema, \
    UserLogoutRequestSchema
from crud.accounts import rollback_decorator, create_new_user, create_activation_token, get_user_by_activation_token, \
    delete_all_activation_tokens, get_activation_token, get_user_by_email, delete_refresh_tokens
from security import JWTManager

router = APIRouter()

DATABASE = Annotated[AsyncSession, Depends(get_db)]
EMAIL_SENDER = Annotated[EmailSender, Depends(get_email_sender)]
JWT_MANAGER = Annotated[JWTManager, Depends(get_jwt_manager)]
ACCESS_TOKEN = Annotated[str, Depends(get_token)]


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
@rollback_decorator(
    error_to_raise=HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This email address is already registered"
    ),
    exceptions=(IntegrityError,)
)
async def register_user(
        request: Request,
        user_data: UserRegistrationRequestSchema,
        background_tasks: BackgroundTasks,
        db: DATABASE,
        email_sender: EMAIL_SENDER
):
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
@rollback_decorator()
async def activate_user(
        activation_data: Annotated[ActivationRequestSchema, Depends(ActivationRequestSchema.as_form)],
        db: DATABASE,
        email_sender: EMAIL_SENDER,
        background_tasks: BackgroundTasks
):
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


@router.post(
    path="/new-activate/",
    response_model=MessageResponseSchema,
    summary="New Activation Token",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Prohibit request if past token is not expired",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "You cannot request a new email yet"
                    }
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "The account already has the is_active = True flag",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Account already active"
                    }
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The request was compromised or the user was removed from the database",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Account not found"
                    }
                }
            }
        }
    }
)
@rollback_decorator()
async def new_activation_token(
        request: Request,
        db: DATABASE,
        email_sender: EMAIL_SENDER,
        background_tasks: BackgroundTasks,
        new_activation_data: Annotated[NewActivationRequestSchema, Depends(NewActivationRequestSchema.as_form)],
):
    activation_token = await get_activation_token(db=db, token=new_activation_data.token)

    if activation_token and activation_token.expires_at > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot request a new email yet"
        )

    user = await get_user_by_email(db=db, email=new_activation_data.email)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if user.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already active")

    await delete_all_activation_tokens(db=db, email=new_activation_data.email)
    token = secrets.token_hex()
    await create_activation_token(db=db, token=token, user=user)
    background_tasks.add_task(
        email_sender.send_activation_email,
        email=new_activation_data.email,
        token=token,
        activation_link=str(request.url_for("activate_user")),
        new_activation_link=str(request.url_for("new_activation_token"))
    )
    await db.commit()

    return {"message": "If the email is correct, the message has been sent"}


@router.post(
    path="/login/",
    response_model=UserLoginResponseSchema,
    summary="User Login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "The user for the provided email address was not found or the password entered is incorrect",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incorrect email or password"
                    }
                }
            }
        }
    }
)
@rollback_decorator()
async def login_user(
        db: DATABASE,
        jwt_manager: JWT_MANAGER,
        user_data: UserLoginRequestSchema
):
    user = await get_user_by_email(db=db, email=user_data.email)
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect email or password")
    data = {
        "user_id": user.id,
    }
    access_token = jwt_manager.create_access_token(data=data)
    refresh_token = await jwt_manager.create_refresh_token(db=db, data=data, user=user)
    await db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post(
    path="/logout/",
    response_model=MessageResponseSchema,
    summary="User Logout",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Refresh token not found in database for current user",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Your refresh token not found"
                    }
                }
            }
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "'Authorization' header was not sent or token invalid",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_header": {
                            "summary": "'Authorization' header was not sent",
                            "value": {"detail": "Authorization header is missing"}
                        },
                        "expired_token": {
                            "summary": "The token in the Authorization header has expired",
                            "value": {
                                "detail": "Token expired"
                            }
                        },
                        "invalid_token": {
                            "summary": "The token in the Authorization header has invalid",
                            "value": {
                                "detail": "Could not validate credentials"
                            }
                        }
                    }
                }
            }
        },
    }
)
@rollback_decorator()
async def logout_user(
        db: DATABASE,
        refresh_data: UserLogoutRequestSchema,
        auth_token: ACCESS_TOKEN,
        jwt_manager: JWT_MANAGER,
):
    token_data = jwt_manager.decode_access_token(token=auth_token)
    is_logout = await delete_refresh_tokens(db=db, token=refresh_data.refresh_token, user_id=token_data["user_id"])
    if not is_logout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Your refresh token not found")
    await db.commit()
    return {"message": "Refresh token has been deleted"}
