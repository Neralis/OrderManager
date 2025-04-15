from typing import List
from ninja import Router
from ninja.errors import HttpError

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

@warehouse_router.delete('/warehouse_delete')
def delete_warehouse(request, warehouse_id: int):
    try:
        warehouse = Warehouse.objects.get(id=warehouse_id)
        warehouse.delete()
        return {"status": "success", "message": f"Склад {warehouse.name} удалён"}
    except Warehouse.DoesNotExist:
        raise HttpError(404, f"Склад с id={warehouse_id} не найден")
