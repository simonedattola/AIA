"""Auth helpers: JWT + bcrypt."""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import bcrypt
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


bearer = HTTPBearer(auto_error=False)

_INSECURE_JWT_SECRETS = frozenset({
    "",
    "change-me-in-production",
    "secret",
    "jwt_secret",
})


def get_jwt_secret() -> str:
    secret = (os.environ.get("JWT_SECRET") or "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET non configurato")
    return secret


def warn_if_insecure_jwt_secret() -> Optional[str]:
    secret = (os.environ.get("JWT_SECRET") or "").strip()
    if secret.lower() in _INSECURE_JWT_SECRETS or len(secret) < 16:
        return (
            "JWT_SECRET debole o di default: impostare un valore casuale lungo "
            "almeno 32 caratteri in produzione."
        )
    return None


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_token(payload: dict) -> str:
    secret = get_jwt_secret()
    algo = os.environ.get("JWT_ALGORITHM", "HS256")
    hours = int(os.environ.get("JWT_EXPIRE_HOURS", "24"))
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(hours=hours)
    return jwt.encode(to_encode, secret, algorithm=algo)


def decode_token(token: str) -> Optional[dict]:
    secret = get_jwt_secret()
    algo = os.environ.get("JWT_ALGORITHM", "HS256")
    try:
        return jwt.decode(token, secret, algorithms=[algo])
    except JWTError:
        return None


async def require_admin(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Token mancante")
    payload = decode_token(creds.credentials)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Token non valido")
    return payload


async def require_member(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Token mancante")
    payload = decode_token(creds.credentials)
    if not payload or payload.get("role") != "member" or not payload.get("memberId"):
        raise HTTPException(status_code=401, detail="Sessione non valida")
    return payload


async def require_admin_or_observer(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """Admin JWT oppure associato osservatore/consiglio."""
    if not creds:
        raise HTTPException(status_code=401, detail="Token mancante")
    payload = decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token non valido")
    if payload.get("role") == "admin":
        return payload
    if payload.get("role") == "member" and payload.get("staffPortal"):
        return payload
    raise HTTPException(status_code=403, detail="Non autorizzato")
