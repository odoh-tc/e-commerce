from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProductIn(BaseModel):
    name: str
    category: str
    original_price: float
    new_price: float
    offer_expiration_date: datetime
    quantity: int
    business_id: Optional[int] = None


class ProductUpdate(BaseModel):
    name: str
    category: str
    original_price: float
    new_price: float
    offer_expiration_date: datetime
    quantity: int
