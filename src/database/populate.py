import re
import random
import asyncio
import pandas as pd
import numpy as np

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_postgresql_db_contextmanager
from database.models.movies import Movie, Certification, Genre, Director, Star
from database.models.accounts import UserGroupModel, UserGroupEnum


class CSVDatabaseSeeder:
    def __init__(self, file_path: str, session_db: AsyncSession) -> None:
        self._csv_file_path = file_path
        self._session_db = session_db

    async def db_is_populated(self) -> bool:
        db_res = await self._session_db.scalars(select(Movie).limit(1))
        return db_res.first() is not None

    def _get_movie_instance(self, record: dict) -> Movie:
        name = record["Series_Title"]
        year = int(record["Released_Year"])
        time = int(re.compile(r"\d+").search(record["Runtime"]).group())
        imdb = float(record["IMDB_Rating"])
        votes = int(record["No_of_Votes"])
        meta_score = (
            int(record["Meta_score"]) if not pd.isna(record["Meta_score"]) else None
        )
        gross = (
            int(record["Gross"].replace(",", ""))
            if not pd.isna(record["Gross"])
            else None
        )
        description = record["Overview"]
        price = Decimal(str(round(random.uniform(10, 100), 2)))

        return Movie(
            name=name,
            year=year,
            time=time,
            imdb=imdb,
            votes=votes,
            meta_score=meta_score,
            gross=gross,
            description=description,
            price=price,
        )

    async def _get_or_create_instance(self, instance, instance_name_field: str):
        model = await self._session_db.scalar(
            select(instance).where(instance.name == instance_name_field)
        )
        if not model:
            model = instance(name=instance_name_field)
            self._session_db.add(model)
            await self._session_db.flush()

        return model

    async def seed(self):
        user_groups = [UserGroupModel(name=name) for name in list(UserGroupEnum)]
        self._session_db.add_all(user_groups)
        await self._session_db.flush()

        MAX_CHUNK = 1000

        records: list = pd.read_csv(self._csv_file_path).to_dict(orient="records")
        chunks_records_generator = np.array_split(
            records, (len(records) // MAX_CHUNK if len(records) > MAX_CHUNK else 1)
        )
        for records in chunks_records_generator:
            movies = []
            for record in records:
                movie = self._get_movie_instance(record)

                genres_names = frozenset(
                    value.strip() for value in record["Genre"].split(",")
                )
                directors_names = frozenset(
                    value.strip() for value in record["Director"].split(",")
                )
                stars_names = frozenset(
                    record[f"Star{number}"] for number in range(1, 5)
                )

                genres, directors, stars = [
                    [
                        await self._get_or_create_instance(
                            instance=instance, instance_name_field=field_name
                        )
                        for field_name in names
                    ]
                    for instance, names in zip(
                        (Genre, Director, Star),
                        (genres_names, directors_names, stars_names),
                    )
                ]
                certification = (
                    await self._get_or_create_instance(
                        instance=Certification,
                        instance_name_field=record["Certificate"],
                    )
                    if not pd.isna(record["Certificate"])
                    else None
                )

                movie.certification = certification
                movie.genres = genres
                movie.directors = directors
                movie.stars = stars

                movies.append(movie)
            self._session_db.add_all(movies)
            await self._session_db.flush()
        await self._session_db.commit()


async def main() -> None:
    from config import get_settings

    settings = get_settings()

    async with get_postgresql_db_contextmanager() as db_session:
        seeder = CSVDatabaseSeeder(
            file_path=settings.PATH_TO_CSV, session_db=db_session
        )

        if await seeder.db_is_populated():
            print("Database populated")
            exit()

        await seeder.seed()
        exit()


asyncio.run(main())
