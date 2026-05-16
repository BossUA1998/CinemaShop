from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field


class CreatePaymentRequestSchema(BaseModel):
    order_id: int = Field(ge=1)


class PaymentsResponseSchema(BaseModel):
    created_at: datetime
    status: str
    amount: Decimal
