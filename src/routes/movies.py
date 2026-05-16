from collections import Counter
from decimal import Decimal
from enum import StrEnum, auto
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, status, HTTPException, Request, Query, BackgroundTasks

from config.dependencies import (
    EMAIL_SENDER,
    ACCESS_TOKEN,
    JWT_MANAGER,
    SETTINGS,
    LIMIT_OFFSET,
    TOKEN_DATA,
)
from crud.accounts import rollback_decorator, get_user_by_id
from database import DATABASE
from crud.movies import (
    get_movies,
    set_reaction,
    set_comment,
    delete_reaction,
    delete_comment,
    set_grade,
    delete_grade,
    insert_favorite_movie,
    delete_favorite_movie,
    get_movie,
    get_all_genres_with_movies_count,
    get_genre_with_movies_by_name,
    set_comment_answer,
    delete_comment_answer,
    set_reaction_to_comment,
    delete_comment_answer_reaction, get_lite_movie,
)
from schemas.accounts import MessageResponseSchema
from schemas.movies import (
    PaginatedMovieResponseSchema,
    ReactionRequestSchema,
    CommentRequestSchema,
    DeleteReactionOrCommentRequestSchema,
    GradeRequestSchema,
    AddToFavoriteRequestSchema,
    MovieDetailResponseSchema,
    GenresResponseSchema,
    GenreDetailResponseSchema,
    CommentAnswerRequestSchema,
    DeleteCommentAnswerRequestSchema,
    CommentReactionRequestSchema,
    DeleteCommentReactionRequestSchema,
)

router = APIRouter()


class SortBy(StrEnum):
    price = auto()
    year = auto()
    votes = auto()


def paginate_movies(movies: list[Movie], request: Request, limit: int) -> dict:
    current_page = int(request.query_params.get("page", 1))
    current_path = request.url.path

    is_next_page = bool(movies.pop(-1) if len(movies) == limit else False)
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


@router.get(
    path="/catalog/",
    response_model=PaginatedMovieResponseSchema,
    summary="Movies Catalog",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "A page value greater than the current position was passed",
            "content": {"application/json": {"example": {"detail": "Page not found"}}},
        }
    },
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
    limit = limit + 1  # Needed to determine the next page

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
            status_code=status.HTTP_404_NOT_FOUND, detail="Movies not found"
        )

    return paginate_movies(movies=movies, request=request, limit=limit)


@router.get(
    path="/catalog/{movie_id}/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Movie Detail",
    responses={},
)
async def movie_detail(
    movie_id: int,
    db: DATABASE,
):
    movie = await get_movie(db=db, movie_id=movie_id)

    reactions = Counter(reaction_model.reaction for reaction_model in movie.reactions)
    likes = reactions[True]
    dislikes = reactions[False]
    movie.likes = likes
    movie.dislikes = dislikes

    return movie


@router.post(
    path="/reaction/",
    response_model=MessageResponseSchema,
    summary="Movies Reaction",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def movie_reaction(
    db: DATABASE,
    token_data: TOKEN_DATA,
    reaction_data: ReactionRequestSchema,
):
    await set_reaction(
        db=db,
        reaction=reaction_data.reaction,
        user_id=token_data["user_id"],
        movie_id=reaction_data.movie_id,
    )
    await db.commit()
    return {"message": "The reaction to the film was recorded"}


@router.post(
    path="/grade/",
    response_model=MessageResponseSchema,
    summary="Movies Grade",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def movie_grade(
    db: DATABASE, token_data: TOKEN_DATA, grade_data: GradeRequestSchema
):
    await set_grade(
        db=db,
        user_id=token_data["user_id"],
        movie_id=grade_data.movie_id,
        grade=grade_data.grade,
    )
    await db.commit()
    return {"message": "The grade was recorded"}


@router.post(
    path="/comment/",
    response_model=MessageResponseSchema,
    summary="Movies Comment",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def movie_comment(
    db: DATABASE,
    token_data: TOKEN_DATA,
    comment_data: CommentRequestSchema,
):
    await set_comment(
        db=db,
        comment=comment_data.comment,
        user_id=token_data["user_id"],
        movie_id=comment_data.movie_id,
    )
    await db.commit()
    return {"message": "The comment was recorded"}


@router.post(
    path="/comment/answer/",
    status_code=status.HTTP_200_OK,
    summary="Movies Comment",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def movie_comment_answer(
    db: DATABASE,
    comment_answer_data: CommentAnswerRequestSchema,
    background_tasks: BackgroundTasks,
    email_sender: EMAIL_SENDER,
    token_data: TOKEN_DATA,
):
    await set_comment_answer(
        db=db,
        user_id=token_data["user_id"],
        movie_id=comment_answer_data.movie_id,
        comment_user_id=comment_answer_data.user_id,
        comment=comment_answer_data.comment,
    )

    comment_user_id = comment_answer_data.user_id
    comment_user = await get_user_by_id(db=db, user_id=comment_user_id)

    movie_id = comment_answer_data.movie_id
    movie = await get_lite_movie(db=db, movie_id=movie_id)

    background_tasks.add_task(
        email_sender.send_reply_notification_to_comment,
        email=comment_user.email,
        comment=comment_answer_data.comment,
        movie_name=movie.name
    )
    await db.commit()
    return {"message": "The answer to comment was recorded"}


@router.delete(
    path="/comment/answer/",
    status_code=status.HTTP_200_OK,
    summary="Movies Comment",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def delete_movie_comment_answer(
    db: DATABASE,
    token_data: TOKEN_DATA,
    comment_answer_data: DeleteCommentAnswerRequestSchema,
):
    await delete_comment_answer(
        db=db,
        user_id=token_data["user_id"],
        movie_id=comment_answer_data.movie_id,
        comment_user_id=comment_answer_data.user_id,
    )
    await db.commit()
    return {"message": "The comment answer was deleted"}


@router.post(
    path="/comment/reaction/",
    status_code=status.HTTP_200_OK,
    summary="Movies Comment",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def movie_comment_reaction(
    db: DATABASE,
    token_data: TOKEN_DATA,
    reaction_data: CommentReactionRequestSchema,
    background_tasks: BackgroundTasks,
    email_sender: EMAIL_SENDER,
):
    await set_reaction_to_comment(
        db=db,
        user_id=token_data["user_id"],
        movie_id=reaction_data.movie_id,
        comment_user_id=reaction_data.user_id,
        reaction=reaction_data.reaction,
    )

    if reaction_data.reaction:
        movie_id = reaction_data.movie_id
        movie = await get_lite_movie(db=db, movie_id=movie_id)

        comment_user_id = reaction_data.user_id
        comment_user = await get_user_by_id(db=db, user_id=comment_user_id)

        background_tasks.add_task(
            email_sender.send_notification_about_reaction_to_comment,
            email=comment_user.email,
            movie_name=movie.name,
        )

    await db.commit()
    return {"message": "The reaction to the comment was recorded"}


@router.delete(
    path="/comment/reaction/",
    status_code=status.HTTP_200_OK,
    summary="Movies Comment",
    response_model=MessageResponseSchema,
)
@rollback_decorator()
async def delete_movie_comment_reaction(
    db: DATABASE,
    token_data: TOKEN_DATA,
    reaction_data: DeleteCommentReactionRequestSchema,
):
    await delete_comment_answer_reaction(
        db=db,
        user_id=token_data["user_id"],
        movie_id=reaction_data.movie_id,
        comment_user_id=reaction_data.user_id,
    )
    await db.commit()
    return {"message": "The reaction to the comment was deleted"}


@router.delete(
    path="/reaction/",
    response_model=MessageResponseSchema,
    summary="Movies Reaction",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def delete_movie_reaction(
    db: DATABASE,
    token_data: TOKEN_DATA,
    data_for_delete: DeleteReactionOrCommentRequestSchema,
):
    await delete_reaction(
        db=db, user_id=token_data["user_id"], movie_id=data_for_delete.movie_id
    )
    await db.commit()
    return {"message": "The reaction was deleted"}


@router.delete(
    path="/comment/",
    response_model=MessageResponseSchema,
    summary="Movies Reaction",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def delete_movie_comment(
    db: DATABASE,
    token_data: TOKEN_DATA,
    data_for_delete: DeleteReactionOrCommentRequestSchema,
):
    await delete_comment(
        db=db, user_id=token_data["user_id"], movie_id=data_for_delete.movie_id
    )
    await db.commit()
    return {"message": "The comment was deleted"}


@router.delete(
    path="/grade/",
    response_model=MessageResponseSchema,
    summary="Movies Grade",
    status_code=status.HTTP_200_OK,
)
@rollback_decorator()
async def delete_movie_grade(
    db: DATABASE,
    token_data: TOKEN_DATA,
    data_for_delete: DeleteReactionOrCommentRequestSchema,
):
    await delete_grade(
        db=db, user_id=token_data["user_id"], movie_id=data_for_delete.movie_id
    )
    await db.commit()
    return {"message": "The grade was deleted"}


@router.post(
    path="/favorite/",
    status_code=status.HTTP_200_OK,
    summary="Movies Favorite",
    response_model=MessageResponseSchema,
)
async def add_movie_to_favorites(
    db: DATABASE,
    token_data: TOKEN_DATA,
    add_to_favorite_data: AddToFavoriteRequestSchema,
):
    await insert_favorite_movie(
        db=db, user_id=token_data["user_id"], movie_id=add_to_favorite_data.movie_id
    )
    await db.commit()
    return {"message": "The favorite movie was added"}


@router.delete(
    path="/favorite/",
    status_code=status.HTTP_200_OK,
    summary="Movies Favorite",
    response_model=MessageResponseSchema,
)
async def delete_movie_with_favorites(
    db: DATABASE,
    token_data: TOKEN_DATA,
    add_to_favorite_data: AddToFavoriteRequestSchema,
):
    await delete_favorite_movie(
        db=db, user_id=token_data["user_id"], movie_id=add_to_favorite_data.movie_id
    )
    await db.commit()
    return {"message": "The favorite movie was deleted"}


@router.get(
    path="/favorite/",
    status_code=status.HTTP_200_OK,
    summary="Movies Favorite",
    response_model=PaginatedMovieResponseSchema,
)
async def get_favorite_movies(
    request: Request,
    db: DATABASE,
    token_data: TOKEN_DATA,
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
    limit = limit + 1

    favorite_movies = await get_movies(
        db=db,
        limit=limit,
        offset=offset,
        user_id_for_select_favorite_movies=token_data["user_id"],
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
    if not favorite_movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Favorite movies not found"
        )
    return paginate_movies(movies=favorite_movies, request=request, limit=limit)


@router.get(
    path="/genres/",
    status_code=status.HTTP_200_OK,
    summary="Movies Genres",
    response_model=list[GenresResponseSchema],
)
async def get_genres(
    db: DATABASE,
):
    genres_with_movies_count = await get_all_genres_with_movies_count(db=db)
    return [
        GenresResponseSchema(genre=genre.name, movies=movies_genre)
        for genre, movies_genre in genres_with_movies_count
    ]


@router.get(
    path="/genres/{genre_name}/",
    status_code=status.HTTP_200_OK,
    summary="Movies Genres",
    response_model=GenreDetailResponseSchema,
)
async def genre_detail(db: DATABASE, genre_name: str):
    return await get_genre_with_movies_by_name(db=db, genre_name=genre_name)
