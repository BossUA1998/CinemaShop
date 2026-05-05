from fastapi import APIRouter, status, HTTPException, Request

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
    responses={}
)
async def movies_catalog(
    request: Request,
    db: DATABASE,
    limit_offset: LIMIT_OFFSET
):
    limit, offset = limit_offset
    limit = limit + 1 # Needed to determine the next page

    movies = await get_movies(db=db, limit=limit, offset=offset)

    if not movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )

    current_page = int(request.query_params.get("page", 1))
    current_path = request.url.path

    is_next_page = bool(
        movies.pop(-1)
        if len(movies) == limit
        else False
    )
    is_previous_page = current_page > 1

    return {
        "next_page": f"{current_path}?page={current_page + 1}" if is_next_page else None,
        "previous_page": f"{current_path}?page={current_page - 1}" if is_previous_page else None,
        "movies": movies,
    }
