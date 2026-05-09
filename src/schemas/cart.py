from pydantic import BaseModel


class AddToCartRequestSchema(BaseModel):
    movie_id: int
