from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.models import TokenData, UserRole
from backend.services.database import get_user_record, create_user_record, update_user_password

# ─── Password Hashing (using bcrypt directly) ────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _hash_password(plain: str) -> str:
    plain_bytes = plain.encode('utf-8')[:72]
    return bcrypt.hashpw(plain_bytes, bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    plain_bytes = plain.encode('utf-8')[:72]
    return bcrypt.checkpw(plain_bytes, hashed.encode())


# ─── User DB Management ───────────────────────────────

def init_default_users():
    if not get_user_record("doctor_user"):
        create_user_record("doctor_user", _hash_password("doctor123"), UserRole.doctor.value)
    if not get_user_record("researcher_user"):
        create_user_record("researcher_user", _hash_password("researcher123"), UserRole.researcher.value)
    if not get_user_record("admin_user"):
        create_user_record("admin_user", _hash_password("admin123"), UserRole.admin.value)

init_default_users()

def authenticate_user(username: str, password: str) -> Optional[dict]:
    record = get_user_record(username)
    if not record or not verify_password(password, record["hashed_password"]):
        return None
    return {"username": record["username"], "role": UserRole(record["role"])}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ─── Dependency: Get Current User ────────────────────────────────────────────

async def get_optional_user(token: str = Depends(oauth2_scheme_optional)) -> Optional[TokenData]:
    if not token:
        return None
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return TokenData(username=username, role=UserRole(role))
    except jwt.PyJWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    user = await get_optional_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(*roles: UserRole):
    """Dependency factory: only allow users with matching roles."""
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker
