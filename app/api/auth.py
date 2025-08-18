from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.models.user import UserCreate, UserLogin, Token, UserResponse
from app.crud.user import create_user, get_user_by_email, get_user_by_id, get_user_by_username
from app.core.security import verify_password, create_access_token, create_refresh_token, verify_token
from app.core.auth import security, get_current_user, UserInDB

router = APIRouter()


def require_admin_role(current_user: UserInDB = Depends(get_current_user)):
    """Dependency to ensure current user has admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required."
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user: UserCreate, 
    current_user: UserInDB = Depends(require_admin_role)
):
    """Register a new user. Only accessible by admin users."""
    # Check if username already exists
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Check if email already exists
    existing_email = await get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = await create_user(user)
    return UserResponse(
        _id=db_user.id,
        name=db_user.name,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        created_at=db_user.created_at
    )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT tokens."""
    user = await get_user_by_username(user_credentials.username)
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh access token using refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Verify user still exists
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role  
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserInDB = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(
        _id=current_user.id,
        name=current_user.name,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at
    )