from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.models.transaction import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionType
from app.models.user import UserInDB
from app.crud.transaction import (
    create_transaction, get_transactions_for_user, get_transaction_by_id,
    update_transaction, delete_transaction
)
from app.crud.user import get_user_by_id
from app.core.auth import get_current_user, require_accountant

router = APIRouter()


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    """Get transactions based on user role."""
    transactions = await get_transactions_for_user(
        current_user.id, 
        current_user.role, 
        skip=skip, 
        limit=limit
    )
    
    # Enrich with user names
    response_transactions = []
    for transaction in transactions:
        user = await get_user_by_id(transaction.user_id)
        response_transactions.append(
            TransactionResponse(
                _id=transaction.id,
                type=transaction.type,
                amount=transaction.amount,
                description=transaction.description,
                user_id=transaction.user_id,
                user_name=user.name if user else "Unknown",
                date=transaction.date
            )
        )
    
    return response_transactions


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction_endpoint(
    transaction: TransactionCreate,
    current_user: UserInDB = Depends(require_accountant)
):
    """Create a new transaction (Accountant/Admin only)."""
    # For deposits, if no user_id specified, use current user
    if transaction.type == TransactionType.DEPOSIT and not transaction.user_id:
        transaction.user_id = current_user.id
    
    # For expenses, user_id should be the accountant who created it
    if transaction.type == TransactionType.EXPENSE:
        transaction.user_id = current_user.id
    
    # Verify user exists if user_id is provided
    if transaction.user_id:
        user = await get_user_by_id(transaction.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user_id"
            )
    
    db_transaction = await create_transaction(transaction)
    user = await get_user_by_id(db_transaction.user_id)
    
    return TransactionResponse(
        _id=db_transaction.id,
        type=db_transaction.type,
        amount=db_transaction.amount,
        description=db_transaction.description,
        user_id=db_transaction.user_id,
        user_name=user.name if user else "Unknown",
        date=db_transaction.date
    )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction_endpoint(
    transaction_id: str,
    transaction_update: TransactionUpdate,
    current_user: UserInDB = Depends(require_accountant)
):
    """Update a transaction (Accountant/Admin only)."""
    db_transaction = await update_transaction(transaction_id, transaction_update)
    if not db_transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    user = await get_user_by_id(db_transaction.user_id)
    
    return TransactionResponse(
        _id=db_transaction.id,
        type=db_transaction.type,
        amount=db_transaction.amount,
        description=db_transaction.description,
        user_id=db_transaction.user_id,
        user_name=user.name if user else "Unknown",
        date=db_transaction.date
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction_endpoint(
    transaction_id: str,
    current_user: UserInDB = Depends(require_accountant)
):
    """Delete a transaction (Accountant/Admin only)."""
    success = await delete_transaction(transaction_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )