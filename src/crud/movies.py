from decimal import Decimal
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

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

    name: str = None,
    description: str = None,
    star: str = None,
    director: str = None,

    year: int = None,
    imdb_rating: float = None,
    time: int = None,
    price: Decimal = None
) -> List[Movie]:
    stmt = (
        select(Movie)
        .order_by(Movie.id.asc())
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

    db_res = await db.scalars(stmt)
    return db_res.all()
