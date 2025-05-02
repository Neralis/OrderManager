from django.contrib import admin
from productApp.models import Product, Stock
from unfold.admin import ModelAdmin

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        'id',
        'name',
        'product_type',
        'product_description',
        'price',
    ]

@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = [
        'product',
        'warehouse',
        'quantity',
    ]


