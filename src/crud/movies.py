from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Select
from sqlalchemy.orm import selectinload

from database.models.movies import Movie


async def get_movies(db: AsyncSession, offset: int, limit: int) -> List[Movie]:
    stmt = (
        select(Movie)
        .order_by(Movie.id.asc())
        .options(
            selectinload(Movie.genres)
        )
        .offset(offset)
        .limit(limit)
    )
    db_res = await db.scalars(stmt)
    return db_res.all()
