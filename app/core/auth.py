from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token
from app.crud.user import get_user_by_id
from app.models.user import UserInDB

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    """Get the current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    if payload.get("type") != "access":
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


def require_role(required_role: str):
    """Dependency to require a specific role."""
    def role_checker(current_user: UserInDB = Depends(get_current_user)):
        if required_role == "admin" and current_user.role not in ["admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        elif required_role == "accountant" and current_user.role not in ["admin", "accountant"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


# Role-specific dependencies
require_admin = require_role("admin")
require_accountant = require_role("accountant")