FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV ALEMBIC_CONFIG=/src/alembic/alembic.ini

RUN python -m pip install poetry

COPY ./poetry.lock /src/poetry/poetry.lock
COPY ./pyproject.toml /src/poetry/pyproject.toml
COPY ./alembic.ini /src/alembic/alembic.ini

WORKDIR /src/poetry

RUN poetry config virtualenvs.create false
RUN poetry install --no-root

WORKDIR /src/commands
COPY ./commands .

WORKDIR /src/fastapi
COPY ./src .
