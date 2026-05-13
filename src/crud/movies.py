from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, update
from sqlalchemy.orm import selectinload, joinedload

from database.models.movies import Movie, Star, Director, Genre, Certification
from database.models.reactions import CommentAnswer, MovieReaction, FavoriteMovie


def _get_fts_query(raw_query: str, model_field):
    query = " & ".join(raw_query.split())
    return func.to_tsvector("english", model_field).op("@@")(
        func.to_tsquery("english", query)
    )


async def get_lite_movie(db: AsyncSession, movie_id: int) -> Optional[Movie]:
    return await db.scalar(select(Movie).where(Movie.id == movie_id))


async def _get_or_create_instance(db: AsyncSession, instance, **fields):
    stmt = (
        select(instance)
        .where(
            *tuple(
                getattr(instance, field_name) == value
                for field_name, value in fields.items()
            )
        )
    )
    loaded_instance = await db.scalar(stmt)

    if not loaded_instance:
        loaded_instance = await db.scalar(
            insert(instance)
            .values(
                **fields
            )
            .on_conflict_do_nothing()
            .returning(instance)
        )
    return loaded_instance


async def get_movies(
    db: AsyncSession,
    offset: int,
    limit: int,
    user_id_for_select_favorite_movies: Optional[int] = None,
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
) -> list[Movie]:
    stmt = (
        select(Movie)
        .options(selectinload(Movie.stars), selectinload(Movie.directors))
        .offset(offset)
        .limit(limit)
    )
    if user_id_for_select_favorite_movies:
        user_id = user_id_for_select_favorite_movies

        stmt = stmt.join(Movie.favorite_movies).where(FavoriteMovie.user_id == user_id)

    if name:
        stmt = stmt.where(Movie.name.ilike(f"%{name}%"))
    if description:
        stmt = stmt.where(_get_fts_query(description, Movie.description))
    if star:
        stmt = stmt.where(Movie.stars.any(_get_fts_query(star, Star.name)))
    if director:
        stmt = stmt.where(Movie.directors.any(_get_fts_query(director, Director.name)))

    for model_field, value in ((Movie.year, year), (Movie.imdb, imdb_rating)):
        if value:
            stmt = stmt.where(model_field == value)

    for model_field, value in ((Movie.time, time), (Movie.price, price)):
        if value:
            stmt = stmt.where(model_field < value)
    if order_by_field:
        model_order_by_field = getattr(Movie, order_by_field)

        if is_desc:
            model_order_by_field = model_order_by_field.desc()

        stmt = stmt.order_by(model_order_by_field)

    db_res = await db.scalars(stmt)
    return db_res.all()


async def get_movie(db: AsyncSession, movie_id: int, get_reactions: bool = True) -> Movie:
    stmt = (
        select(Movie)
        .options(
            joinedload(Movie.certification),
            selectinload(Movie.stars),
            selectinload(Movie.directors),
            selectinload(Movie.genres)
        )
        .where(Movie.id == movie_id)
    )
    if get_reactions:
        stmt = stmt.options(
            selectinload(Movie.reactions).selectinload(MovieReaction.comment_answers),
        )
    return await db.scalar(stmt)


async def update_movie(db: AsyncSession, movie_id: int, **kwargs) -> Movie:
    if not kwargs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field is required"
        )

    movie_fields = frozenset(
        column
        for column in Movie.__table__.columns.keys()
        if column not in {"uuid", "id"}
    )
    nullable_fields = frozenset(column.key for column in Movie.__table__.columns if column.nullable)
    field_to_update = {
        key: kwargs[key]
        for key in movie_fields & kwargs.keys()
    }

    movie = await get_movie(db=db, movie_id=movie_id, get_reactions=False)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    for field_name, value in field_to_update.items():
        if value or field_name in nullable_fields:
            setattr(movie, field_name, value)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Field '{field_name}' cannot be null or not valid"
            )
    genres, director, stars, certification = (
        kwargs.get("genres"),
        kwargs.get("director"),
        kwargs.get("stars"),
        kwargs.get("certification")
    )
    if genres:
        loaded_genres = [
            genre
            for genre_name in genres
            if (genre := await _get_or_create_instance(db=db, instance=Genre, name=genre_name))
        ]
        if loaded_genres:
            movie.genres = loaded_genres

    if stars:
        loaded_stars = [
            star
            for star_full_name in stars
            if (star := await _get_or_create_instance(db=db, instance=Star, name=star_full_name))
        ]
        if loaded_stars:
            movie.stars = loaded_stars

    if director:
        loaded_director = await _get_or_create_instance(db=db, instance=Director, name=director)
        if loaded_director:
            movie.directors = [loaded_director]

    if certification:
        loaded_certification = await _get_or_create_instance(db=db, instance=Certification, name=certification)
        if loaded_certification:
            movie.certification = loaded_certification

    db.add(movie)
    await db.flush()
    return movie


async def create_movie(db: AsyncSession, **kwargs) -> Optional[Movie]:
    movie_fields = frozenset(
        column
        for column in Movie.__table__.columns.keys()
        if column not in {"uuid", "id"}
    )
    not_nullable_movie_fields = frozenset(
        column.key
        for column in Movie.__table__.columns
        if not column.nullable and column.key not in {"id", "uuid"}
    )

    not_set_fields = not_nullable_movie_fields.difference(kwargs.keys())
    if not_set_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Required fields [{", ".join(not_set_fields)}]"
        )

    fields_to_create = {
        field: kwargs[field]
        for field in movie_fields
        if field in kwargs and (
            kwargs[field] is not None
            or field not in not_nullable_movie_fields
        )
    }
    movie = await db.scalar(
        insert(Movie)
        .values(**fields_to_create)
        .on_conflict_do_nothing()
        .returning(Movie)
    )

    genres, director, stars, certification = (
        kwargs.get("genres"),
        kwargs.get("director"),
        kwargs.get("stars"),
        kwargs.get("certification")
    )
    if any((genres, director, stars)) and movie:
        return await update_movie(db=db, movie_id=movie.id, genres=genres, director=director, stars=stars, certification=certification)
    return movie


async def delete_movie(db: AsyncSession, movie_id: int) -> Optional[Movie]:
    from crud.orders import _get_is_purchased_movie
    if await _get_is_purchased_movie(db=db, movie_id=movie_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The film had already been bought by someone"
        )
    await db.scalar(
        delete(Movie)
        .where(Movie.id == movie_id)
    )


async def set_reaction(
    db: AsyncSession, reaction: bool, user_id: int, movie_id: int
) -> None:
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


async def set_comment_answer(
    db: AsyncSession, comment: str, user_id: int, movie_id: int, comment_user_id: int
) -> None:
    await db.execute(
        insert(CommentAnswer)
        .values(
            comment=comment,
            user_id=user_id,
            movie_reaction_movie_id=movie_id,
            movie_reaction_user_id=comment_user_id,
        )
        .on_conflict_do_update(
            index_elements=[
                "user_id",
                "movie_reaction_user_id",
                "movie_reaction_movie_id",
            ],
            set_={"comment": comment},
        )
    )


async def set_reaction_to_comment(
    db: AsyncSession, user_id: int, movie_id: int, comment_user_id: int, reaction: bool
) -> None:
    await db.execute(
        insert(CommentAnswer)
        .values(
            reaction=reaction,
            user_id=user_id,
            movie_reaction_movie_id=movie_id,
            movie_reaction_user_id=comment_user_id,
        )
        .on_conflict_do_update(
            index_elements=[
                "user_id",
                "movie_reaction_user_id",
                "movie_reaction_movie_id",
            ],
            set_={"reaction": reaction},
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


async def get_reaction_model(
    db: AsyncSession, user_id: int, movie_id: int
) -> MovieReaction:
    reaction_model = await db.scalar(
        select(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )
    if not reaction_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reaction not found"
        )
    return reaction_model


async def _delete_reaction_model(db: AsyncSession, user_id: int, movie_id: int) -> None:
    await db.execute(
        delete(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )


async def _update_reaction_model(
    db: AsyncSession, user_id: int, movie_id: int, field_to_set_null: str
) -> None:
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


reaction_field_already_none = lambda message: HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail=message
)


async def delete_reaction(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.reaction is None:
        raise reaction_field_already_none(message="The reaction was not recorded")
    if reaction_model.comment is None and reaction_model.grade is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(
            db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="reaction"
        )


async def delete_comment(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.comment is None:
        raise reaction_field_already_none(message="The comment was not recorded")
    if reaction_model.reaction is None and reaction_model.grade is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(
            db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="comment"
        )


async def delete_grade(db: AsyncSession, user_id: int, movie_id: int) -> None:
    reaction_model = await get_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    if reaction_model.grade is None:
        raise reaction_field_already_none(message="The grade was not recorded")
    if reaction_model.reaction is None and reaction_model.comment is None:
        await _delete_reaction_model(db=db, user_id=user_id, movie_id=movie_id)
    else:
        await _update_reaction_model(
            db=db, user_id=user_id, movie_id=movie_id, field_to_set_null="grade"
        )


async def get_comment_answer(
    db: AsyncSession, user_id: int, movie_id: int, comment_user_id: int
) -> Optional[CommentAnswer]:
    comment_answer = await db.scalar(
        select(CommentAnswer).where(
            CommentAnswer.user_id == user_id,
            CommentAnswer.movie_reaction_user_id == comment_user_id,
            CommentAnswer.movie_reaction_movie_id == movie_id,
        )
    )
    if not comment_answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment answer not found"
        )
    return comment_answer


async def _delete_comment_answer(
    db: AsyncSession, user_id: int, movie_id: int, comment_user_id: int
) -> None:
    await db.execute(
        delete(CommentAnswer).where(
            CommentAnswer.user_id == user_id,
            CommentAnswer.movie_reaction_user_id == comment_user_id,
            CommentAnswer.movie_reaction_movie_id == movie_id,
        )
    )


async def _update_comment_answer(
    db: AsyncSession,
    user_id: int,
    movie_id: int,
    comment_user_id: int,
    field_to_set_null: str,
) -> None:
    kwargs = {field_to_set_null: None}
    await db.execute(
        update(CommentAnswer)
        .where(
            CommentAnswer.user_id == user_id,
            CommentAnswer.movie_reaction_user_id == comment_user_id,
            CommentAnswer.movie_reaction_movie_id == movie_id,
        )
        .values(**kwargs)
    )


async def delete_comment_answer(
    db: AsyncSession, user_id: int, movie_id: int, comment_user_id: int
) -> None:
    comment_answer = await get_comment_answer(
        db=db, user_id=user_id, movie_id=movie_id, comment_user_id=comment_user_id
    )
    if comment_answer.comment is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Comment answer was not recorded",
        )
    if comment_answer.reaction is None:
        await _delete_comment_answer(
            db=db, user_id=user_id, movie_id=movie_id, comment_user_id=comment_user_id
        )
    else:
        await _update_comment_answer(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
            comment_user_id=comment_user_id,
            field_to_set_null="comment",
        )


async def delete_comment_answer_reaction(
    db: AsyncSession, user_id: int, movie_id: int, comment_user_id: int
) -> None:
    comment_answer = await get_comment_answer(
        db=db, user_id=user_id, movie_id=movie_id, comment_user_id=comment_user_id
    )
    if comment_answer.reaction is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Reaction was not recorded"
        )
    if comment_answer.comment is None:
        await _delete_comment_answer(
            db=db, user_id=user_id, movie_id=movie_id, comment_user_id=comment_user_id
        )
    else:
        await _update_comment_answer(
            db=db,
            user_id=user_id,
            movie_id=movie_id,
            comment_user_id=comment_user_id,
            field_to_set_null="reaction",
        )


async def insert_favorite_movie(db: AsyncSession, user_id: int, movie_id: int) -> None:
    db_res = await db.execute(
        insert(FavoriteMovie)
        .values(
            user_id=user_id,
            movie_id=movie_id,
        )
        .on_conflict_do_nothing()
    )
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The movie has already been added to your favorites",
        )


async def delete_favorite_movie(db: AsyncSession, user_id: int, movie_id: int) -> None:
    db_res = await db.execute(
        delete(FavoriteMovie).where(
            FavoriteMovie.user_id == user_id,
            FavoriteMovie.movie_id == movie_id,
        )
    )
    if db_res.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The movie has not been added to your favorites",
        )


async def get_all_genres_with_movies_count(db: AsyncSession) -> list[Genre]:
    return await db.execute(
        select(Genre, func.count(Movie.id)).outerjoin(Genre.movies).group_by(Genre.id)
    )


async def get_genre_with_movies_by_name(db: AsyncSession, genre_name: str) -> Genre:
    return await db.scalar(
        select(Genre)
        .where(func.lower(Genre.name) == genre_name.lower())
        .options(selectinload(Genre.movies))
    )
