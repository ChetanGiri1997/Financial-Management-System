from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def get_database():
    return db.database


async def connect_to_mongo():
    """Create database connection"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.database = db.client[settings.DATABASE_NAME]
    
    # Create indexes
    await create_indexes()


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()


async def create_indexes():
    """Create database indexes"""
    users_collection = db.database.users
    transactions_collection = db.database.transactions
    
    # Users indexes
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("username", unique=True)
    
    # Transactions indexes
    await transactions_collection.create_index("user_id")
    await transactions_collection.create_index("date")
    await transactions_collection.create_index("type")