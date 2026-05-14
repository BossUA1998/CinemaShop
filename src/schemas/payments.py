from pydantic import BaseModel, Field


class CreatePaymentRequestSchema(BaseModel):
    order_id: int = Field(ge=1)
