import secrets
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    try:
        return ph.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, TypeError):
        return False

def generate_token() -> str:
    return secrets.token_urlsafe(48)

def password_is_strong(password: str) -> bool:
    return len(password) >= 10 and any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password)
