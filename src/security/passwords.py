from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError, InvalidHashError

password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=32 * 1024,  # 32 mb
)


def hash_password(raw_password: str) -> str:
    return password_hasher.hash(raw_password)


def verify_password(raw_password: str, hashed_password: str) -> bool:
    try:
        password_hasher.verify(hashed_password, raw_password)
        return True
    except (VerificationError, VerifyMismatchError, InvalidHashError):
        return False
