from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.user import UserCreate, UserUpdate, UserResponse, UserInDB
from app.crud.user import create_user, get_user_by_username, get_users, get_user_by_id, update_user, delete_user, get_user_by_email
from app.core.auth import require_admin

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserInDB = Depends(require_admin)
):
    """Get all users (Admin only)."""
    users = await get_users(skip=skip, limit=limit)
    return [
        UserResponse(
            _id=user.id,
            name=user.name,
            username=user.username,
            email=user.email,
            role=user.role,
            created_at=user.created_at
        )
        for user in users
    ]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user: UserCreate,
    current_user: UserInDB = Depends(require_admin)
):
    """Create a new user (Admin only)."""
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


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(require_admin)
):
    """Update a user (Admin only)."""
    db_user = await update_user(user_id, user_update)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        _id=db_user.id,
        name=db_user.name,
        username=db_user.username,
        email=db_user.email,
        role=db_user.role,
        created_at=db_user.created_at
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    current_user: UserInDB = Depends(require_admin)
):
    """Delete a user (Admin only)."""
    success = await delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )