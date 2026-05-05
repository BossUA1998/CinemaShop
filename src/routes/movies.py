from typing import List, Annotated

from fastapi import APIRouter, status
from fastapi.params import Query

from config.dependencies import EMAIL_SENDER, ACCESS_TOKEN, JWT_MANAGER
from database import DATABASE
from crud.movies import get_movies
from schemas.movies import MovieResponseSchema

router = APIRouter()


@router.get(
    path="/catalog/",
    response_model=List[MovieResponseSchema],
    summary="Movies Catalog",
    status_code=status.HTTP_200_OK,
    responses={}
)
async def movies_catalog(
    db: DATABASE,
    page: int = Query(default=1, ge=1)
):
    return await get_movies(db=db)
