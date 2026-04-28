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


class MessageResponseSchema(BaseModel):
    message: str


class ActivationRequestSchema(BaseModel):
    token: str

    @classmethod
    def as_form(
            cls,
            token: Annotated[str, Form()],
    ) -> "ActivationRequestSchema":
        return cls(token=token)


class NewActivationRequestSchema(BaseModel):
    token: str
    email: EmailStr

    @classmethod
    def as_form(
            cls,
            token: Annotated[str, Form()],
            email: Annotated[str, Form()],
    ) -> "NewActivationRequestSchema":
        return cls(token=token, email=email)


class UserLoginRequestSchema(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class UserLogoutRequestSchema(BaseModel):
    refresh_token: str
