from ninja import Schema
from typing import List, Optional

from pydantic.v1 import validator


class OrderItemIn(Schema):
    product_id: int
    quantity: int

class OrderIn(Schema):
    warehouse_id: int
    items: List[OrderItemIn]
    client_name: str  # 🆕
    destination_address: str  # 🆕
    comment: Optional[str] = None  # 🆕


class OrderItemOut(Schema):
    product_id: int
    name: str
    quantity: int
    price: float

class OrderOut(Schema):
    id: int
    status: str
    created_at: str
    warehouse: int
    qr_code: Optional[str]
    items: List[OrderItemOut]
    total_price: float
    client_name: str  # 🆕
    destination_address: str  # 🆕
    comment: Optional[str] = None  # 🆕
    total_price: float  # 🆕
    cancellation_reason: str | None = None


class OrderStatusIn(Schema):
    status: str

class ReturnItemIn(Schema):
    product_id: int
    quantity: int

    @validator('quantity')
    def quantity_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError('Quantity must be positive')
        return value

class ReturnIn(Schema):
    reason: Optional[str] = None
    items: List[ReturnItemIn]

class ReturnItemOut(Schema):
    product_id: int
    name: str
    quantity: int

class ReturnOut(Schema):
    order_id: int
    reason: Optional[str]
    created_at: str
    items: List[ReturnItemOut]

class OrderCancellationIn(Schema):  # 🆕 NEW
    reason: str
