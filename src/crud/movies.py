from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, Select
from sqlalchemy.orm import selectinload

from database.models.movies import Movie


def paginate_db_request(stmt: Select, offset: int, limit: int) -> Select:
    offset, limit = max(0, offset), max(0, limit)
    return stmt.offset(offset).limit(limit)


async def get_movies(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Movie]:
    sql = (
        select(Movie)
        .order_by(Movie.id.desc())
        .options(
            selectinload(Movie.genres)
        )
    )

    stmt = paginate_db_request(
        stmt=sql,
        offset=skip,
        limit=limit,
    )
    db_res = await db.scalars(stmt)
    return db_res.all()
