from django.conf import settings
from django.conf.urls.static import static
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
