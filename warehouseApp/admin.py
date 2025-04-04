from django.contrib import admin
from warehouseApp.models import Warehouse
from unfold.admin import ModelAdmin

@admin.register(Warehouse)
class ProductAdmin(ModelAdmin):
    list_display = [
        'name',
        'address'
    ]


