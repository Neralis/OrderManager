from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from productApp.api import product_router

api = NinjaAPI()

api.add_router('/products/', product_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
