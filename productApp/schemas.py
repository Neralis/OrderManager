from ninja import Schema

# Схема для вывода данных о продукте
class ProductOut(Schema):
    id: int
    name: str
    product_type: str
    price: float

# Схема для ввода данных о продукте
class ProductIn(Schema):
    name: str
    product_type: str
    price: float