from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from fastapi import HTTPException, status
from .config import settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)

def create_access_token(subject: str, organization_id: int) -> str:
    if len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be set to a strong random value (32+ characters)")
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": subject, "org": organization_id, "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes)}, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token") from exc
