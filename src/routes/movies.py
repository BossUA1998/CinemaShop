from decimal import Decimal
from enum import StrEnum, auto
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, status, HTTPException, Request, Query

from config.dependencies import EMAIL_SENDER, ACCESS_TOKEN, JWT_MANAGER, SETTINGS, LIMIT_OFFSET
from crud.accounts import rollback_decorator
from database import DATABASE
from crud.movies import get_movies, set_reaction, set_comment
from schemas.accounts import MessageResponseSchema
from schemas.movies import PaginatedMovieResponseSchema, ReactionRequestSchema, CommentRequestSchema

router = APIRouter()


class SortBy(StrEnum):
    price = auto()
    year = auto()
    votes = auto()


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

    # search
    name: Optional[str] = Query(default=None),
    description: Optional[str] = Query(default=None),
    star: Optional[str] = Query(default=None),
    director: Optional[str] = Query(default=None),

    # filters
    year: Optional[int] = Query(default=None),
    rating: Optional[float] = Query(default=None),
    time: Optional[int] = Query(default=None),
    price: Optional[Decimal] = Query(default=None),

    # order by
    sort_by: Optional[SortBy] = Query(default=None),
    desc: bool = Query(default=False),
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

        order_by_field=sort_by,
        is_desc=desc,
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


@router.post(
    path="/reaction/",
    response_model=MessageResponseSchema,
    summary="Movies Reaction",
    status_code=status.HTTP_200_OK,
    responses={}
)
@rollback_decorator()
async def movie_reaction(
    db: DATABASE,
    token: ACCESS_TOKEN,
    jwt_manager: JWT_MANAGER,
    reaction_data: ReactionRequestSchema,
):
    token_data = jwt_manager.decode_access_token(token=token)
    await set_reaction(
        db=db,
        reaction=reaction_data.reaction,
        user_id=token_data["user_id"],
        movie_id=reaction_data.movie_id
    )
    await db.commit()
    return {"message": "The reaction to the film was recorded"}


@router.post(
    path="/comment/",
    response_model=MessageResponseSchema,
    summary="Movies Comment",
    status_code=status.HTTP_200_OK,
    responses={}
)
@rollback_decorator()
async def movie_comment(
    db: DATABASE,
    token: ACCESS_TOKEN,
    jwt_manager: JWT_MANAGER,
    comment_data: CommentRequestSchema,
):
    token_data = jwt_manager.decode_access_token(token=token)
    await set_comment(
        db=db,
        comment=comment_data.comment,
        user_id=token_data["user_id"],
        movie_id=comment_data.movie_id
    )
    await db.commit()
    return {"message": "The comment was recorded"}
