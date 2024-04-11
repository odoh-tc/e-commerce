from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OrderStatus(str, Enum):
    pending = 'pending'
    processing = 'processing'
    shipped = 'shipped'
    delivered = 'delivered'
    cancelled = 'cancelled'


class OrderBase(BaseModel):
    product_id: int
    quantity: Optional[int] = 1

class OrderIn(OrderBase):
    order_date: datetime
    # total_price: float
    # status: OrderStatus = OrderStatus.pending

class OrderUpdate(BaseModel):
    quantity: int