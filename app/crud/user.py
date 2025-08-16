from typing import List, Optional
from bson import ObjectId
from app.db.mongodb import get_database
from app.models.user import UserCreate, UserUpdate, UserInDB
from app.core.security import get_password_hash
from datetime import datetime


async def get_user_by_username(username: str) -> Optional[UserInDB]:
    """Get user by username."""
    database = await get_database()
    user_doc = await database.users.find_one({"username": username})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Get user by email."""
    database = await get_database()
    user_doc = await database.users.find_one({"email": email})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    """Get user by ID."""
    if not ObjectId.is_valid(user_id):
        return None
    
    database = await get_database()
    user_doc = await database.users.find_one({"_id": ObjectId(user_id)})
    if user_doc:
        user_doc["_id"] = str(user_doc["_id"])
        return UserInDB(**user_doc)
    return None


async def create_user(user: UserCreate) -> UserInDB:
    """Create a new user."""
    database = await get_database()
    user_dict = user.dict()
    user_dict["password_hash"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    
    result = await database.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    return UserInDB(**user_dict)


async def get_users(skip: int = 0, limit: int = 100) -> List[UserInDB]:
    """Get all users with pagination."""
    database = await get_database()
    cursor = database.users.find().skip(skip).limit(limit)
    users = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        users.append(UserInDB(**doc))
    return users


async def update_user(user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
    """Update a user."""
    if not ObjectId.is_valid(user_id):
        return None
    
    database = await get_database()
    update_dict = {k: v for k, v in user_update.dict().items() if v is not None}
    
    if "password" in update_dict:
        update_dict["password_hash"] = get_password_hash(update_dict.pop("password"))
    
    if update_dict:
        await database.users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": update_dict}
        )
    
    return await get_user_by_id(user_id)


async def delete_user(user_id: str) -> bool:
    """Delete a user."""
    if not ObjectId.is_valid(user_id):
        return False
    
    database = await get_database()
    result = await database.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0


async def get_user_count() -> int:
    """Get total user count."""
    database = await get_database()
    return await database.users.count_documents({})