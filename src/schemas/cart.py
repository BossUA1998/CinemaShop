from pydantic import BaseModel
from schemas.base_schemas import _RawSchemaWithMovieId


class AddToCartRequestSchema(_RawSchemaWithMovieId): ...


class DeleteFromCartRequestSchema(_RawSchemaWithMovieId): ...
