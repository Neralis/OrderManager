from typing import Optional

from ninja import Schema

class WarehouseIn(Schema):
    name: str
    address: str

class WarehouseOut(Schema):
    id: int
    address: str
    name: str

class WarehouseUpdate(Schema):
    name: Optional[str] = None
    address: Optional[str] = None