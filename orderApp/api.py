# order_api.py
from ninja import Router
from django.shortcuts import get_object_or_404
from django.core.files import File
from django.db import transaction
from django.http import HttpRequest
from io import BytesIO
import qrcode
from ninja.errors import HttpError

from orderApp.models import Order, OrderItem, Return, ReturnItem
from orderApp.schemas import (
    OrderOut, OrderIn, OrderItemOut,
    OrderStatusIn, ReturnOut, ReturnIn,
    ReturnItemOut
)
from productApp.models import Product, Stock
from warehouseApp.models import Warehouse

order_router = Router(tags=["Заказы"])

@order_router.post('/order_create', response=OrderOut)
def create_order(request: HttpRequest, data: OrderIn):
    warehouse = get_object_or_404(Warehouse, id=data.warehouse_id)

    for item in data.items:
        product = get_object_or_404(Product, id=item.product_id)
        stock = get_object_or_404(Stock, product=product, warehouse=warehouse)
        if stock.quantity < item.quantity:
            raise HttpError(400, f"Недостаточно товара {product.name}: нужно {item.quantity}, есть {stock.quantity}")

    with transaction.atomic():
        order = Order.objects.create(warehouse=warehouse)

        # Генерация QR-кода
        qr_data = request.build_absolute_uri(f"/api/orders/order/{order.id}")
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        file_name = f"order_{order.id}_qr.png"
        order.qr_code.save(file_name, File(buffer), save=True)
        buffer.close()

        items_out = []
        total_price = 0

        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            stock = get_object_or_404(Stock, product=product, warehouse=warehouse)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price
            )

            stock.quantity -= item.quantity
            stock.save()

            items_out.append(OrderItemOut(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity,
                price=product.price
            ))
            total_price += item.quantity * product.price

        return OrderOut(
            id=order.id,
            status=order.status,
            created_at=order.created_at.isoformat(),
            warehouse=order.warehouse.id,
            qr_code=order.qr_code.url if order.qr_code else None,
            total_price=total_price,
            items=items_out
        )

@order_router.get("/order/{order_id}", response=OrderOut)
def get_order(request: HttpRequest, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    items_out = []
    total_price = 0

    for item in order.items.select_related('product'):
        items_out.append(OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity,
            price=item.price
        ))
        total_price += item.quantity * item.price

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        total_price=total_price,
        items=items_out
    )

@order_router.get("/order", response=list[OrderOut])
def list_orders(request: HttpRequest):
    orders = Order.objects.prefetch_related('items__product')
    result = []

    for order in orders:
        items_out = []
        total_price = 0

        for item in order.items.all():
            items_out.append(OrderItemOut(
                product_id=item.product.id,
                name=item.product.name,
                quantity=item.quantity,
                price=item.price
            ))
            total_price += item.quantity * item.price

        result.append(OrderOut(
            id=order.id,
            status=order.status,
            created_at=order.created_at.isoformat(),
            warehouse=order.warehouse.id,
            qr_code=order.qr_code.url if order.qr_code else None,
            total_price=total_price,
            items=items_out
        ))

    return result

@order_router.patch('/order/{order_id}/status', response=OrderOut)
def update_order_status(request: HttpRequest, order_id: int, data: OrderStatusIn):
    order = get_object_or_404(Order, id=order_id)
    order.status = data.status
    order.save()

    items_out = []
    total_price = 0

    for item in order.items.select_related('product'):
        items_out.append(OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity,
            price=item.price
        ))
        total_price += item.quantity * item.price

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        total_price=total_price,
        items=items_out
    )

@order_router.post("/order/{order_id}/return", response=ReturnOut)
def create_return(request: HttpRequest, order_id: int, data: ReturnIn):
    order = get_object_or_404(Order, id=order_id)
    if order.status not in ['new', 'processing', 'completed']:
        raise HttpError(400, "Невозможно оформить возврат в текущем статусе.")

    if Return.objects.filter(order=order).exists():
        raise HttpError(400, "Уже есть возврат для этого заказа.")

    order_items = {item.product.id: item.quantity for item in order.items.all()}
    total_returned_quantity = 0
    total_order_quantity = sum(order_items.values())

    for item in data.items:
        if item.product_id not in order_items:
            raise HttpError(400, "Некорректный товар.")
        if item.quantity > order_items[item.product_id]:
            raise HttpError(400, "Количество превышает заказ.")

        total_returned_quantity += item.quantity

    with transaction.atomic():
        return_obj = Return.objects.create(order=order, reason=data.reason or "")
        return_items_out = []

        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            stock = get_object_or_404(Stock, product=product, warehouse=order.warehouse)

            ReturnItem.objects.create(
                return_obj=return_obj,
                product=product,
                quantity=item.quantity
            )

            stock.quantity += item.quantity
            stock.save()

            return_items_out.append(ReturnItemOut(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity
            ))

        if total_returned_quantity == total_order_quantity:
            order.status = 'returned'
            order.save()

    return ReturnOut(
        order_id=order.id,
        reason=return_obj.reason,
        created_at=return_obj.created_at.isoformat(),
        items=return_items_out
    )
