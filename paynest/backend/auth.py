from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from supabase import Client

from database import get_db, get_settings

router = APIRouter(tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    name: str
    photo: Optional[str] = None


class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    photo: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


def create_access_token(data: Dict[str, Any], expires_in_minutes: int = 60 * 24) -> str:
    settings = get_settings()
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def upsert_user(db: Client, payload: LoginRequest) -> Dict[str, Any]:
    existing = db.table("users").select("*").eq("email", payload.email).limit(1).execute()
    if existing.data:
        user = existing.data[0]
        db.table("users").update({"name": payload.name, "photo": payload.photo}).eq("id", user["id"]).execute()
        user["name"] = payload.name
        user["photo"] = payload.photo
        return user

    inserted = (
        db.table("users")
        .insert({"name": payload.name, "email": payload.email, "photo": payload.photo})
        .execute()
    )
    return inserted.data[0]


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Client = Depends(get_db)) -> TokenResponse:
    user = upsert_user(db, payload)
    token = create_access_token({"sub": user["id"], "email": user["email"]})
    return TokenResponse(access_token=token, user=User(**user))


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Client = Depends(get_db),
) -> Dict[str, Any]:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    response = db.table("users").select("*").eq("id", user_id).limit(1).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return response.data[0]
