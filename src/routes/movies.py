from decimal import Decimal
from urllib.parse import urlencode

from fastapi import APIRouter, status, HTTPException, Request, Query

from config.dependencies import EMAIL_SENDER, ACCESS_TOKEN, JWT_MANAGER, SETTINGS, LIMIT_OFFSET
from database import DATABASE
from crud.movies import get_movies
from schemas.movies import PaginatedMovieResponseSchema

router = APIRouter()


@router.get(
    path="/catalog/",
    response_model=PaginatedMovieResponseSchema,
    summary="Movies Catalog",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "A page value greater than the current position was passed",
            "content": {
                "application/json": {
                    "example": {"detail": "Page not found"}
                }
            }
        }
    }
)
async def movies_catalog(
    request: Request,
    db: DATABASE,
    limit_offset: LIMIT_OFFSET,

    # query params
    name: str = Query(default=None),
    description: str = Query(default=None),
    star: str = Query(default=None),
    director: str = Query(default=None),

    year: int = Query(default=None),
    rating: float = Query(default=None),
    time: int = Query(default=None),
    price: Decimal = Query(default=None),
):
    limit, offset = limit_offset
    limit = limit + 1 # Needed to determine the next page

    movies = await get_movies(
        db=db,
        limit=limit,
        offset=offset,
        name=name,
        description=description,
        star=star,
        director=director,
        year=year,
        imdb_rating=rating,
        time=time,
        price=price,
    )

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movies not found"
        )

    current_page = int(request.query_params.get("page", 1))
    current_path = request.url.path

    is_next_page = bool(
        movies.pop(-1)
        if len(movies) == limit
        else False
    )
    is_previous_page = current_page > 1

    base_params = dict(request.query_params)
    base_params.pop("page", None)

    return {
        "next_page": (
            f"{current_path}?{urlencode(base_params | {"page": current_page + 1})}"
            if is_next_page
            else None
        ),
        "previous_page": (
            f"{current_path}?{urlencode(base_params | {"page": current_page - 1})}"
            if is_previous_page
            else None
        ),
        "movies": movies,
    }
