from decimal import Decimal
from typing import List, Optional

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
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
