from ninja import Schema

class WarehouseIn(Schema):
    name: str
    address: str

class WarehouseOut(Schema):
    id: int
    address: str
    name: str
    address: str