from typing import List, Optional, Dict, Any
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.transaction import TransactionCreate, TransactionUpdate, TransactionInDB, TransactionType
from app.models.user import UserRole
from datetime import datetime
from pymongo import DESCENDING


async def create_transaction(transaction: TransactionCreate) -> TransactionInDB:
    """Create a new transaction."""
    database = await get_database()
    transaction_dict = transaction.dict()
    
    result = await database.transactions.insert_one(transaction_dict)
    transaction_dict["_id"] = str(result.inserted_id)
    return TransactionInDB(**transaction_dict)


async def get_transactions_for_user(
    user_id: str, 
    user_role: str,
    skip: int = 0, 
    limit: int = 100
) -> List[TransactionInDB]:
    """Get transactions based on user role."""
    database = await get_database()
    
    if user_role in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        # Admin and accountant can see all transactions
        cursor = database.transactions.find()
    else:
        # Regular users can see ALL transactions for transparency (read-only)
        # This gives users full visibility into deposits and expenses
        cursor = database.transactions.find()
    
    cursor = cursor.sort("date", DESCENDING).skip(skip).limit(limit)
    
    transactions = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        transactions.append(TransactionInDB(**doc))
    
    return transactions


async def get_transaction_by_id(
    transaction_id: str, 
    user_id: str = None, 
    user_role: str = None
) -> Optional[TransactionInDB]:
    """Get transaction by ID with role-based access control."""
    if not ObjectId.is_valid(transaction_id):
        return None
    
    database = await get_database()
    doc = await database.transactions.find_one({"_id": ObjectId(transaction_id)})
    
    if not doc:
        return None
    
    # If user role is provided, check access permissions
    if user_role and user_role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        # Regular users can view any transaction (transparency)
        # but cannot modify - this check is for viewing only
        pass
    
    doc["_id"] = str(doc["_id"])
    return TransactionInDB(**doc)


async def update_transaction(
    transaction_id: str, 
    transaction_update: TransactionUpdate,
    user_role: str
) -> Optional[TransactionInDB]:
    """Update a transaction - only admin and accountant can modify."""
    if user_role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        return None  # Unauthorized
    
    if not ObjectId.is_valid(transaction_id):
        return None
    
    database = await get_database()
    update_dict = {k: v for k, v in transaction_update.dict().items() if v is not None}
    
    if update_dict:
        await database.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": update_dict}
        )
    
    return await get_transaction_by_id(transaction_id)


async def delete_transaction(transaction_id: str, user_role: str) -> bool:
    """Delete a transaction - only admin and accountant can delete."""
    if user_role not in [UserRole.ADMIN, UserRole.ACCOUNTANT]:
        return False  # Unauthorized
    
    if not ObjectId.is_valid(transaction_id):
        return False
    
    database = await get_database()
    result = await database.transactions.delete_one({"_id": ObjectId(transaction_id)})
    return result.deleted_count > 0


async def can_manage_transaction(user_role: str) -> bool:
    """Check if user can create, update, or delete transactions."""
    return user_role in [UserRole.ADMIN, UserRole.ACCOUNTANT]


async def get_financial_summary(user_role: str = None) -> Dict[str, Any]:
    """Get financial summary with totals and monthly breakdown."""
    database = await get_database()
    
    # All users can view financial summary for transparency
    # but this could be restricted if needed
    
    # Aggregate pipeline for summary
    pipeline = [
        {
            "$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    
    result = {}
    async for doc in database.transactions.aggregate(pipeline):
        result[doc["_id"]] = {
            "total": doc["total"],
            "count": doc["count"]
        }
    
    # Calculate balance
    total_deposits = result.get("deposit", {}).get("total", 0)
    total_expenses = result.get("expense", {}).get("total", 0)
    balance = total_deposits - total_expenses
    
    # Monthly breakdown
    monthly_pipeline = [
        {
            "$group": {
                "_id": {
                    "year": {"$year": "$date"},
                    "month": {"$month": "$date"},
                    "type": "$type"
                },
                "total": {"$sum": "$amount"}
            }
        },
        {"$sort": {"_id.year": -1, "_id.month": -1}}
    ]
    
    monthly_data = {}
    async for doc in database.transactions.aggregate(monthly_pipeline):
        key = f"{doc['_id']['year']}-{doc['_id']['month']:02d}"
        if key not in monthly_data:
            monthly_data[key] = {"deposits": 0, "expenses": 0}
        monthly_data[key][f"{doc['_id']['type']}s"] = doc["total"]
    
    return {
        "total_deposits": total_deposits,
        "total_expenses": total_expenses,
        "balance": balance,
        "deposit_count": result.get("deposit", {}).get("count", 0),
        "expense_count": result.get("expense", {}).get("count", 0),
        "monthly_breakdown": monthly_data
    }


async def get_user_deposits(user_id: str, requesting_user_role: str = None) -> Dict[str, Any]:
    """Get user-specific deposit report."""
    database = await get_database()
    
    # Admin and accountant can view any user's deposits
    # Regular users can view all deposits for transparency
    
    pipeline = [
        {"$match": {"user_id": user_id, "type": "deposit"}},
        {
            "$group": {
                "_id": None,
                "total_deposits": {"$sum": "$amount"},
                "deposit_count": {"$sum": 1},
                "transactions": {"$push": "$$ROOT"}
            }
        }
    ]
    
    result = await database.transactions.aggregate(pipeline).to_list(1)
    
    if result:
        data = result[0]
        transactions = []
        for t in data["transactions"]:
            t["_id"] = str(t["_id"])
            transactions.append(t)
        
        return {
            "user_id": user_id,
            "total_deposits": data["total_deposits"],
            "deposit_count": data["deposit_count"],
            "transactions": transactions
        }
    
    return {
        "user_id": user_id,
        "total_deposits": 0,
        "deposit_count": 0,
        "transactions": []
    }