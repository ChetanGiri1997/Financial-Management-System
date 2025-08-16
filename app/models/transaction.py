from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from decimal import Decimal


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    EXPENSE = "expense"


class TransactionBase(BaseModel):
    type: TransactionType
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    date: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(TransactionBase):
    user_id: Optional[str] = None  # Will be set by the system for deposits


class TransactionUpdate(BaseModel):
    type: Optional[TransactionType] = None
    amount: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    date: Optional[datetime] = None


class TransactionInDB(TransactionBase):
    id: str = Field(alias="_id")
    user_id: str
    
    class Config:
        populate_by_name = True


class TransactionResponse(TransactionBase):
    id: str = Field(alias="_id")
    user_id: str
    user_name: Optional[str] = None
    
    class Config:
        populate_by_name = True