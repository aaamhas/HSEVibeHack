from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import User
from backend.schemas import TokenResponse, UserResponse
from backend.config.redis_config import (
    get_redis_client,
    store_refresh_token,
    get_refresh_token,
    delete_refresh_token,
)

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class DevLoginRequest(BaseModel):
    """Development login - for testing without Google OAuth"""
    email: str
    name: str = "Test User"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token (short-lived: 30 min)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> User:
    """
    Extract and verify user from JWT access token.
    Use as dependency: current_user: User = Depends(get_current_user)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    payload = verify_token(token)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/dev-login")
async def dev_login(request: DevLoginRequest, db: Session = Depends(get_db)):
    """
    Development login endpoint - bypasses Google OAuth for testing.

    Usage:
    POST /auth/dev-login
    {
        "email": "test@example.com",
        "name": "Test User"
    }
    """
    try:
        # Create or update user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            user = User(
                email=request.email,
                name=request.name,
                google_id=None,
                access_token=None,
                refresh_token=None,
                token_expiry=None,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        # Create JWT access token
        jwt_access_token = create_access_token({"sub": str(user.id)})

        # Generate refresh token UUID and store in Redis
        refresh_token_uuid = str(uuid.uuid4())
        redis_client = await get_redis_client()

        # Store mapping: refresh_token_uuid -> user_id
        await redis_client.setex(
            f"refresh_token_uuid:{refresh_token_uuid}",
            7 * 24 * 60 * 60,  # 7 days
            str(user.id)
        )

        # Store refresh token with user_id:uuid key
        await store_refresh_token(user.id, refresh_token_uuid, refresh_token_uuid)

        return {
            "access_token": jwt_access_token,
            "refresh_token": refresh_token_uuid,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": 7 * 24 * 60 * 60,
            "user": UserResponse.model_validate(user),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")



@router.post("/refresh")
async def refresh_access_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Refresh JWT access token using refresh token from Redis"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    refresh_token_uuid = token
    redis_client = await get_redis_client()

    # Look up user_id from UUID
    user_id_key = f"refresh_token_uuid:{refresh_token_uuid}"
    user_id = await redis_client.get(user_id_key)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = int(user_id)

    # Verify token exists
    token_exists = await get_refresh_token(user_id, refresh_token_uuid)
    if not token_exists:
        raise HTTPException(status_code=401, detail="Refresh token not found or expired")

    # Load user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new access token
    new_access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Logout - deletes all refresh tokens for user from Redis"""
    redis_client = await get_redis_client()

    # Delete all refresh tokens for this user
    keys_pattern = f"refresh_token:{current_user.id}:*"
    keys = await redis_client.keys(keys_pattern)

    deleted_count = 0
    if keys:
        deleted_count = await redis_client.delete(*keys)

    return {
        "message": "Logged out successfully",
        "user_id": current_user.id,
        "tokens_revoked": deleted_count,
    }
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
import uuid
from typing import Optional
from dotenv import load_dotenv

from backend.database import get_db
from backend.models import User
from backend.schemas import TokenResponse, UserResponse
from backend.config.redis_config import (
    get_redis_client,
    store_refresh_token,
    get_refresh_token,
    delete_refresh_token,
)

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class DevLoginRequest(BaseModel):
    """Development login - for testing without Google OAuth"""
    email: str
    name: str = "Test User"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token (short-lived: 30 min)"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> User:
    """
    Extract and verify user from JWT access token.
    Use as dependency: current_user: User = Depends(get_current_user)
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    payload = verify_token(token)

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/dev-login")
async def dev_login(request: DevLoginRequest, db: Session = Depends(get_db)):
    """
    Development login endpoint - bypasses Google OAuth for testing.

    Usage:
    POST /auth/dev-login
    {
        "email": "test@example.com",
        "name": "Test User"
    }
    """
    try:
        # Create or update user
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            user = User(
                email=request.email,
                name=request.name,
                google_id=None,
                access_token=None,
                refresh_token=None,
                token_expiry=None,
            )
            db.add(user)

        db.commit()
        db.refresh(user)

        # Create JWT access token
        jwt_access_token = create_access_token({"sub": str(user.id)})

        # Generate refresh token UUID and store in Redis
        refresh_token_uuid = str(uuid.uuid4())
        redis_client = await get_redis_client()

        # Store mapping: refresh_token_uuid -> user_id
        await redis_client.setex(
            f"refresh_token_uuid:{refresh_token_uuid}",
            7 * 24 * 60 * 60,  # 7 days
            str(user.id)
        )

        # Store refresh token with user_id:uuid key
        await store_refresh_token(user.id, refresh_token_uuid, refresh_token_uuid)

        return {
            "access_token": jwt_access_token,
            "refresh_token": refresh_token_uuid,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": 7 * 24 * 60 * 60,
            "user": UserResponse.model_validate(user),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Login failed: {str(e)}")



@router.post("/refresh")
async def refresh_access_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Refresh JWT access token using refresh token from Redis"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    refresh_token_uuid = token
    redis_client = await get_redis_client()

    # Look up user_id from UUID
    user_id_key = f"refresh_token_uuid:{refresh_token_uuid}"
    user_id = await redis_client.get(user_id_key)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = int(user_id)

    # Verify token exists
    token_exists = await get_refresh_token(user_id, refresh_token_uuid)
    if not token_exists:
        raise HTTPException(status_code=401, detail="Refresh token not found or expired")

    # Load user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create new access token
    new_access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: Optional[str] = Header(None)
):
    """Logout - deletes all refresh tokens for user from Redis"""
    redis_client = await get_redis_client()

    # Delete all refresh tokens for this user
    keys_pattern = f"refresh_token:{current_user.id}:*"
    keys = await redis_client.keys(keys_pattern)

    deleted_count = 0
    if keys:
        deleted_count = await redis_client.delete(*keys)

    return {
        "message": "Logged out successfully",
        "user_id": current_user.id,
        "tokens_revoked": deleted_count,
    }
