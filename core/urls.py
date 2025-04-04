from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from productApp.api import product_router
from warehouseApp.api import warehouse_router

api = NinjaAPI()

api.add_router('/products/', product_router)
api.add_router('/warehouses/', warehouse_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
