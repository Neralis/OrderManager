from typing import Optional

from ninja import Schema
from warehouseApp.models import Warehouse
from warehouseApp.schemas import WarehouseOut


# Схема для вывода данных о продукте
class ProductOut(Schema):
    id: int
    name: str
    product_type: str
    price: float
    warehouse: int
    product_description: Optional[str]

# Схема для ввода данных о продукте
class ProductIn(Schema):
    name: str
    product_type: str
    price: float
    warehouse: int
    product_description: Optional[str]

    class Config:
        from_attributes = True

class ProductImageIn(Schema):
    product_id: int
    alt_text: Optional[str] = None

class ProductImageOut(Schema):
    id: int
    product: int
    image_url: str
    alt_text: Optional[str]
    uploaded_at: str