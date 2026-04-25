from jose import jwt
from datetime import datetime, timezone, timedelta


class TokenManager:
    def __init__(
            self,
            access_secret_key: str,
            refresh_secret_key: str,
            algorithm: str = "HS256",
            access_token_expire_minutes: int = 30,
            refresh_token_expire_days: int = 7
    ):
        self.__access_secret_key = access_secret_key
        self.__refresh_secret_key = refresh_secret_key
        self._algorithm = algorithm
        self._access_token_expire_minutes = access_token_expire_minutes
        self._refresh_token_expire_days = refresh_token_expire_days

    def _encode_token(self, key: str, expires_at: float, data: dict):
        data["exp"] = expires_at
        return jwt.encode(
            claims=data,
            key=key,
            algorithm=self._algorithm,
        )

    def _decode_token(self, token: str, key: str):
        return jwt.decode(token=token, key=key, algorithms=self._algorithm)

    def create_access_token(self, data: dict):
        expires_delta = datetime.now(timezone.utc) + timedelta(minutes=self._access_token_expire_minutes)
        return self._encode_token(key=self.__access_secret_key, expires_at=expires_delta, data=data)

    def create_refresh_token(self, data: dict):
        expires_delta = datetime.now(timezone.utc) + timedelta(days=self._refresh_token_expire_days)
        return self._encode_token(key=self.__refresh_secret_key, expires_at=expires_delta, data=data)

    def decode_access_token(self, token: str) -> dict:
        return self._decode_token(token=token, key=self.__access_secret_key)

    def decode_refresh_token(self, token: str) -> dict:
        return self._decode_token(token=token, key=self.__refresh_secret_key)
