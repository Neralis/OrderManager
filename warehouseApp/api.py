from typing import List
from ninja import Router
from warehouseApp.models import Warehouse
from warehouseApp.schemas import WarehouseIn, WarehouseOut

warehouse_router = Router(tags=['Склады'])

@warehouse_router.get('/warehouse_list',response=List[WarehouseOut])
def get_warehouses(request):
    warehouses = Warehouse.objects.all()
    return warehouses

@warehouse_router.post('/warehouse_create', response=WarehouseOut)
def create_warehouse(request, data: WarehouseIn):
    warehouse = Warehouse(
        name=data.name,
        address=data.address
    )
    warehouse.save()
    return warehouse