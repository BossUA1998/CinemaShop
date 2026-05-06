from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload

from database.models import MovieReaction
from database.models.movies import Movie, Star, Director


def _get_fts_query(raw_query: str, model_field):
    query = " & ".join(raw_query.split())
    return func.to_tsvector("english", model_field).op("@@")(
        func.to_tsquery("english", query)
    )


async def get_movies(
    db: AsyncSession,
    offset: int,
    limit: int,

    name: Optional[str] = None,
    description: Optional[str] = None,
    star: Optional[str] = None,
    director: Optional[str] = None,

    year: Optional[int] = None,
    imdb_rating: Optional[float] = None,
    time: int = Optional[None],
    price: Optional[Decimal] = None,

    order_by_field: Optional[str] = None,
    is_desc: bool = False,
) -> List[Movie]:
    stmt = (
        select(Movie)
        .options(
            selectinload(Movie.stars),
            selectinload(Movie.directors)
        )
        .offset(offset)
        .limit(limit)
    )

    if name:
        stmt = stmt.where(
            Movie.name.ilike(f"%{name}%")
        )
    if description:
        stmt = stmt.where(
            _get_fts_query(description, Movie.description)
        )
    if star:
        stmt = stmt.where(
            Movie.stars.any(
                _get_fts_query(star, Star.name)
            )
        )
    if director:
        stmt = stmt.where(
            Movie.directors.any(
                _get_fts_query(director, Director.name)
            )
        )

    for model_field, value in (
            (Movie.year, year),
            (Movie.imdb, imdb_rating)
    ):
        if value:
            stmt = stmt.where(
                model_field == value
            )

    for model_field, value in (
            (Movie.time, time),
            (Movie.price, price)
    ):
        if value:
            stmt = stmt.where(
                model_field < value
            )
    if order_by_field:
        model_order_by_field = getattr(Movie, order_by_field)

        if is_desc:
            model_order_by_field = model_order_by_field.desc()

        stmt = stmt.order_by(
            model_order_by_field
        )

    db_res = await db.scalars(stmt)
    return db_res.all()


async def set_reaction(db: AsyncSession, reaction: bool, user_id: int, movie_id: int) -> None:
    await db.execute(
        insert(MovieReaction)
        .values(
            reaction=reaction,
            user_id=user_id,
            movie_id=movie_id,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "movie_id"],
            set_={"reaction": reaction},
        )
    )


async def set_comment(db: AsyncSession, comment: str, user_id: int, movie_id: int):
    await db.execute(
        insert(MovieReaction)
        .values(
            comment=comment,
            user_id=user_id,
            movie_id=movie_id,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "movie_id"],
            set_={"comment": comment},
        )
    )


async def set_grade(db: AsyncSession, grade: int, user_id: int, movie_id: int) -> None:
    await db.execute(
        insert(MovieReaction)
        .values(
            grade=grade,
            user_id=user_id,
            movie_id=movie_id,
        )
        .on_conflict_do_update(
            index_elements=["user_id", "movie_id"],
            set_={"grade": grade},
        )
    )


async def get_reaction_model(db: AsyncSession, user_id: int, movie_id: int) -> MovieReaction:
    reaction_model = await db.scalar(
        select(MovieReaction)
        .where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )
    if not reaction_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found"
        )
    return reaction_model


async def _delete_reaction_model(db: AsyncSession, user_id: int, movie_id: int) -> None:
    await db.execute(
        delete(MovieReaction)
        .where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )


async def _update_reaction_model(db: AsyncSession, user_id: int, movie_id: int, field_to_set_null: str) -> None:
    kwargs = {field_to_set_null: None}
    await db.execute(
        update(MovieReaction)
        .where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
        .values(
            **kwargs,
        )
    )


async def delete_reaction(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.comment is None and reaction_model.grade is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="reaction")


async def delete_comment(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.reaction is None and reaction_model.grade is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="comment")


async def delete_grade(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.reaction is None and reaction_model.comment is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="grade")
