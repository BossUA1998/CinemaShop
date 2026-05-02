import secrets
from datetime import datetime, timezone

from typing import Annotated

from fastapi import APIRouter, status, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError

from schemas.accounts import (
    UserRegistrationResponseSchema,
    UserRegistrationRequestSchema,
    MessageResponseSchema,
    ActivationRequestSchema,
    NewActivationRequestSchema,
    UserLoginResponseSchema,
    UserLoginRequestSchema,
    UserLogoutRequestSchema,
    RefreshRequestSchema,
    RefreshResponseSchema,
    ResetPasswordRequestSchema,
    ResetPasswordVerifyRequestSchema,
)
from crud.accounts import (
    rollback_decorator,
    create_new_user,
    create_activation_token,
    get_user_by_activation_token,
    delete_all_activation_tokens,
    get_activation_token,
    get_user_by_email,
    delete_refresh_tokens,
    get_refresh_token,
    create_password_reset_token,
    get_password_reset_token,
    delete_password_reset_tokens,
)
from config.dependencies import EMAIL_SENDER, ACCESS_TOKEN, JWT_MANAGER
from database import DATABASE

router = APIRouter()


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
                    "example": {"detail": "This email address is already registered"}
                }
            },
        },
    },
)
@rollback_decorator(
    error_to_raise=HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="This email address is already registered",
    ),
    exceptions=(IntegrityError,),
)
async def register_user(
    request: Request,
    user_data: UserRegistrationRequestSchema,
    background_tasks: BackgroundTasks,
    db: DATABASE,
    email_sender: EMAIL_SENDER,
):
    user = await create_new_user(db=db, user_data=user_data)

    token = secrets.token_hex()
    await create_activation_token(db=db, token=token, user=user)

    background_tasks.add_task(
        email_sender.send_activation_email,
        email=user.email,
        token=token,
        activation_link=str(request.url_for("activate_user")),
        new_activation_link=str(request.url_for("new_activation_token")),
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
            "content": {"application/json": {"example": {"detail": "Token not found"}}},
        }
    },
)
@rollback_decorator()
async def activate_user(
    request: Request,
    activation_data: Annotated[ActivationRequestSchema, Depends()],
    db: DATABASE,
    email_sender: EMAIL_SENDER,
    background_tasks: BackgroundTasks,
):
    token = await get_activation_token(db=db, token=activation_data.token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
        )

    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This token has expired"
        )

    user = await get_user_by_activation_token(db=db, token=activation_data.token)
    user.is_active = True

    await delete_all_activation_tokens(db=db, email=user.email)

    background_tasks.add_task(
        email_sender.send_activation_complete_email,
        email=user.email,
        login_link=request.url_for("login_user"),
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
                    "example": {"detail": "You cannot request a new email yet"}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "The account already has the is_active = True flag",
            "content": {
                "application/json": {"example": {"detail": "Account already active"}}
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "The request was compromised or the user was removed from the database",
            "content": {
                "application/json": {"example": {"detail": "Account not found"}}
            },
        },
    },
)
@rollback_decorator()
async def new_activation_token(
    request: Request,
    db: DATABASE,
    email_sender: EMAIL_SENDER,
    background_tasks: BackgroundTasks,
    new_activation_data: Annotated[NewActivationRequestSchema, Depends()],
):
    activation_token = await get_activation_token(
        db=db, token=new_activation_data.token
    )

    if activation_token and activation_token.expires_at > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot request a new email yet",
        )

    user = await get_user_by_email(db=db, email=new_activation_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already active"
        )

    await delete_all_activation_tokens(db=db, email=new_activation_data.email)
    token = secrets.token_hex()
    await create_activation_token(db=db, token=token, user=user)
    background_tasks.add_task(
        email_sender.send_activation_email,
        email=new_activation_data.email,
        token=token,
        activation_link=str(request.url_for("activate_user")),
        new_activation_link=str(request.url_for("new_activation_token")),
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
                    "example": {"detail": "Incorrect email or password"}
                }
            },
        }
    },
)
@rollback_decorator()
async def login_user(
    db: DATABASE, jwt_manager: JWT_MANAGER, user_data: UserLoginRequestSchema
):
    user = await get_user_by_email(db=db, email=user_data.email)
    if not user or not user.verify_password(user_data.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Incorrect email or password"
        )
    data = {
        "user_id": user.id,
    }
    access_token = jwt_manager.create_access_token(data=data, is_refresh=False)
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
                    "example": {"detail": "Your refresh token not found"}
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "'Authorization' header was not sent or token invalid",
            "content": {
                "application/json": {
                    "examples": {
                        "missing_header": {
                            "summary": "'Authorization' header was not sent",
                            "value": {"detail": "Authorization header is missing"},
                        },
                        "expired_token": {
                            "summary": "The token in the Authorization header has expired",
                            "value": {"detail": "Token expired"},
                        },
                        "invalid_token": {
                            "summary": "The token in the Authorization header has invalid",
                            "value": {"detail": "Could not validate credentials"},
                        },
                    }
                }
            },
        },
    },
)
@rollback_decorator()
async def logout_user(
    db: DATABASE,
    refresh_data: UserLogoutRequestSchema,
    auth_token: ACCESS_TOKEN,
    jwt_manager: JWT_MANAGER,
):
    token_data = jwt_manager.decode_access_token(token=auth_token)
    is_logout = await delete_refresh_tokens(
        db=db, token=refresh_data.refresh_token, user_id=token_data["user_id"]
    )
    if not is_logout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Your refresh token not found"
        )
    await db.commit()
    return {"message": "Refresh token has been deleted"}


@router.post(
    path="/refresh/",
    response_model=RefreshResponseSchema,
    summary="User Refresh",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Refresh token expired",
            "content": {
                "application/json": {"example": {"detail": "Refresh token expired"}}
            },
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Refresh token not valid or not found in database",
            "content": {
                "application/json": {"example": {"detail": "Refresh token not found"}}
            },
        },
    },
)
async def refresh_user(
    db: DATABASE,
    refresh_data: RefreshRequestSchema,
    jwt_manager: JWT_MANAGER,
):
    refresh_token_model = await get_refresh_token(
        db=db, token=refresh_data.refresh_token
    )
    if not refresh_token_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Refresh token not found"
        )
    if refresh_token_model.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token expired",
        )
    data = {"user_id": refresh_token_model.user_id}
    return {"access_token": jwt_manager.create_access_token(data=data, is_refresh=True)}


@router.post(
    path="/reset-password/",
    response_model=MessageResponseSchema,
    summary="User Reset",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def reset_password(
    request: Request,
    db: DATABASE,
    background_tasks: BackgroundTasks,
    reset_data: ResetPasswordRequestSchema,
    email_sender: EMAIL_SENDER,
):
    user = await get_user_by_email(db=db, email=reset_data.email)
    if user:
        if reset_data.old_password and user.verify_password(reset_data.old_password):
            user.password = reset_data.new_password
            await db.commit()
            return {"message": "Password has been reset"}

        await delete_password_reset_tokens(db=db, user=user)

        password_reset_token = secrets.token_hex()
        await create_password_reset_token(db=db, token=password_reset_token, user=user)

        background_tasks.add_task(
            email_sender.send_password_reset_email,
            email=user.email,
            token=password_reset_token,
            new_password=reset_data.new_password,
            password_reset_link=str(request.url_for("reset_password_verify")),
        )

        await db.commit()

    return {"message": "If the email is correct, check your mailbox"}


@router.post(
    path="/reset-password/verify/",
    response_model=MessageResponseSchema,
    summary="User Reset",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_403_FORBIDDEN: {
            "description": "Password reset token has problems",
            "content": {
                "application/json": {
                    "examples": {
                        "Not found token": {
                            "summary": "The token was removed from the database either due to its unusability or due to user actions",
                            "value": {"detail": "Password reset token not found"},
                        },
                        "Expired token": {
                            "summary": "The token has expired and will be deleted soon",
                            "value": {"detail": "Password reset token expired"},
                        },
                        "Invalid token": {
                            "summary": "The token has an incorrect structure or this is an attempt to forge the token",
                            "value": {"detail": "Password reset token is invalid"},
                        },
                    }
                }
            },
        }
    },
)
@rollback_decorator()
async def reset_password_verify(
    request: Request,
    db: DATABASE,
    background_tasks: BackgroundTasks,
    reset_data: Annotated[ResetPasswordVerifyRequestSchema, Depends()],
    email_sender: EMAIL_SENDER,
):
    user = await get_user_by_email(db=db, email=reset_data.email)
    token = await get_password_reset_token(db=db, token=reset_data.token)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password reset token not found",
        )
    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Password reset token expired",
        )
    if user and (token.user_id == user.id):
        user.password = reset_data.new_password
        await delete_refresh_tokens(db=db, email=user.email)
        await db.commit()

        background_tasks.add_task(
            email_sender.send_password_reset_complete_email,
            email=user.email,
            login_link=str(request.url_for("login_user")),
        )

        return {"message": "Password has been reset"}
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Password reset token is invalid",
    )
