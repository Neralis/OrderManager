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
    list_filter = [
        'product_type',
        'price',
    ]
    search_fields = ['name', 'product_description']
    list_per_page = 20
    show_full_result_count = True

@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = [
        'product',
        'warehouse',
        'quantity',
    ]
    list_filter = [
        'warehouse',
        'quantity',
    ]
    search_fields = ['product__name', 'warehouse']
    list_per_page = 20
    show_full_result_count = True


