from pydantic import BaseModel, Field


class _RawSchemaWithMovieId(BaseModel):
    movie_id: int = Field(ge=1)


class MessageResponseSchema(BaseModel):
    message: str
