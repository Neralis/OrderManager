from django.contrib import admin
from productApp.models import Product
from unfold.admin import ModelAdmin

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        'name',
        'product_type',
        'price'
    ]


