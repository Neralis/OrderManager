from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Order, OrderItem, Return, ReturnItem
from warehouseApp.models import Warehouse
from productApp.models import Product


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["id", "client_name", "status", "warehouse", "total_price", "created_at"]
    list_editable = ["status"]  # Делаем поле status редактируемым в списке
    list_filter = ["status", "warehouse", "created_at"]
    search_fields = ["client_name", "destination_address", "comment"]
    list_select_related = ["warehouse"]  # Оптимизация запросов
    readonly_fields = ["created_at", "total_price"]
    fieldsets = (
        (None, {
            "fields": ("status", "warehouse", "client_name", "destination_address")
        }),
        ("Дополнительно", {
            "fields": ("qr_code", "comment", "cancellation_reason", "total_price", "created_at")
        }),
    )

    class OrderItemInline(admin.TabularInline):
        model = OrderItem
        extra = 1
        fields = ["product", "quantity", "price"]
        autocomplete_fields = ["product"]

    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ["order", "product", "quantity", "price"]
    list_filter = ["order__status", "product"]
    search_fields = ["product__name", "order__client_name"]
    list_select_related = ["order", "product"]
    autocomplete_fields = ["product", "order"]


@admin.register(Return)
class ReturnAdmin(ModelAdmin):
    list_display = ["order", "created_at", "reason_short"]
    list_filter = ["created_at", "order__status"]
    search_fields = ["order__client_name", "reason"]
    list_select_related = ["order"]
    readonly_fields = ["created_at"]

    def reason_short(self, obj):
        return obj.reason[:50] + ("..." if len(obj.reason) > 50 else "")
    reason_short.short_description = "Причина"

    class ReturnItemInline(admin.TabularInline):
        model = ReturnItem
        extra = 1
        fields = ["product", "quantity"]
        autocomplete_fields = ["product"]

    inlines = [ReturnItemInline]


@admin.register(ReturnItem)
class ReturnItemAdmin(ModelAdmin):
    list_display = ["return_obj", "product", "quantity"]
    list_filter = ["return_obj__order__status", "product"]
    search_fields = ["product__name", "return_obj__order__client_name"]
    list_select_related = ["return_obj", "product"]
    autocomplete_fields = ["product", "return_obj"]