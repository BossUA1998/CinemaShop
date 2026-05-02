from typing import Annotated

from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import (
    get_postgresql_db as get_db,
)
DATABASE = Annotated[AsyncSession, Depends(get_db)]
from database.validators import accounts as accounts_validators
