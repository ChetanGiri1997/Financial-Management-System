from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import UserInDB
from app.crud.transaction import get_financial_summary, get_user_deposits
from app.crud.user import get_user_by_id
from app.core.auth import get_current_user, require_accountant

router = APIRouter()


@router.get("/summary", response_model=Dict[str, Any])
async def get_financial_summary_endpoint(
    current_user: UserInDB = Depends(require_accountant)
):
    """Get financial summary (Accountant/Admin only)."""
    return await get_financial_summary()


@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_report(
    user_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """Get user-specific deposits report."""
    # Users can only see their own reports unless they are admin/accountant
    if current_user.role not in ["admin", "accountant"] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify user exists
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    report = await get_user_deposits(user_id)
    report["user_name"] = user.name
    return report