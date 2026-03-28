from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends

from backend.auth import authenticate_user, create_access_token, _hash_password
from backend.models import Token, UserLogin
from backend.services.database import create_user_record, update_user_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(form_data: UserLogin):
    """Login with username, password, and role selection."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if user["role"] != form_data.role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User does not have the selected role: {form_data.role.value}",
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"].value}
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user["role"],
        username=user["username"],
    )

@router.post("/register")
async def register(form_data: UserLogin):
    """Register a new user."""
    hashed = _hash_password(form_data.password)
    success = create_user_record(form_data.username, hashed, form_data.role.value)
    if not success:
        raise HTTPException(status_code=400, detail="Username already exists")
    return {"message": "User registered successfully."}

@router.post("/reset-password")
async def reset_password(form_data: UserLogin):
    """Reset password (requires valid username and role matching for simplicity in prototype)."""
    # Simple verification that the user exists and their role matches
    from backend.services.database import get_user_record
    record = get_user_record(form_data.username)
    if not record or record["role"] != form_data.role.value:
        raise HTTPException(status_code=400, detail="Invalid username or role configuration")
    
    hashed = _hash_password(form_data.password)
    success = update_user_password(form_data.username, hashed)
    if not success:
        raise HTTPException(status_code=500, detail="Internal error updating password")
    return {"message": "Password updated successfully."}
