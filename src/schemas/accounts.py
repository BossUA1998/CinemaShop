from typing import Annotated

from pydantic import BaseModel, EmailStr, field_validator
from database import accounts_validators
from fastapi import Form


class BaseEmailPasswordSchema(BaseModel):
    email: EmailStr
    password: str

    model_config = {"from_attributes": True}

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        return accounts_validators.validate_password_strength(value)


class UserRegistrationRequestSchema(BaseEmailPasswordSchema):
    pass


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr


class ActivationRequestSchema:
    def __init__(
        self,
        token: Annotated[str, Form()],
    ):
        self.token = token


class NewActivationRequestSchema:
    def __init__(
        self,
        token: Annotated[str, Form()],
        email: Annotated[EmailStr, Form()],
    ):
        self.token = token
        self.email = email


class UserLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class BaseRefreshToken(BaseModel):
    refresh_token: str


class BaseAccessToken(BaseModel):
    access_token: str


class UserLoginResponseSchema(BaseRefreshToken, BaseAccessToken): ...


class UserLogoutRequestSchema(BaseRefreshToken): ...


class RefreshRequestSchema(BaseRefreshToken): ...


class RefreshResponseSchema(BaseAccessToken): ...


class ResetPasswordRequestSchema(BaseModel):
    email: EmailStr
    new_password: str
    old_password: str = None


class ResetPasswordVerifyRequestSchema:
    def __init__(
        self,
        email: Annotated[EmailStr, Form()],
        new_password: Annotated[str, Form()],
        token: Annotated[str, Form()],
    ):
        self.email = email
        self.new_password = new_password
        self.token = token
