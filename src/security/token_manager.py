from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timezone, timedelta

from jose.exceptions import JWTClaimsError
from sqlalchemy.ext.asyncio import AsyncSession


class TokenManager:
    """
    func for create access token is sync
    func for create refresh tokes is async and takes async session to database
    """

    def __init__(
        self,
        access_secret_key: str,
        refresh_secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ):
        self.__access_secret_key = access_secret_key
        self.__refresh_secret_key = refresh_secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

    def _encode_token(self, key: str, data: dict, expires_at: float = None):
        data_copy = data.copy()
        if expires_at:
            data_copy["exp"] = expires_at
        return jwt.encode(
            claims=data_copy,
            key=key,
            algorithm=self._algorithm,
        )

    def _decode_token(self, token: str, key: str):
        try:
            data = jwt.decode(token=token, key=key, algorithms=self._algorithm)
            if data.keys() != {"exp", "user_id"}:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                )
            return data
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except (JWTError, JWTClaimsError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def create_access_token(self, data: dict, is_refresh: bool = False):
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=(
                self._access_token_expire_minutes
                if not is_refresh
                else self._access_token_expire_minutes // 2
            )
        )
        return self._encode_token(
            key=self.__access_secret_key, expires_at=expires_at.timestamp(), data=data
        )

    async def create_refresh_token(self, data: dict, user: "User", db: AsyncSession):
        from crud.accounts import create_refresh_token as crud_create_refresh_token

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=self._refresh_token_expire_days
        )
        data["exp"] = expires_at.timestamp()
        token = self._encode_token(
            key=self.__refresh_secret_key,
            data=data,
        )
        await crud_create_refresh_token(
            token=token, db=db, user=user, expires_at=expires_at
        )
        return token

    def decode_access_token(self, token: str) -> dict:
        return self._decode_token(token=token, key=self.__access_secret_key)

    def decode_refresh_token(self, token: str) -> dict:
        return self._decode_token(token=token, key=self.__refresh_secret_key)
