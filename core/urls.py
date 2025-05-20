from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from orderApp.api import order_router
from productApp.api import product_router
from reportApp.api import report_router
from userApp.api import auth_router
from warehouseApp.api import warehouse_router

api = NinjaAPI(
    title="API Системы управления складами и заказами",
    version="1.0.0",
)

api.add_router('/products/', product_router)
api.add_router('/warehouses/', warehouse_router)
api.add_router('/auth/', auth_router)
api.add_router('/orders/', order_router)
api.add_router('/report/', report_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
