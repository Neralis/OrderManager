from django.shortcuts import get_object_or_404
from ninja import Router
from orderApp.models import Order, OrderItem, Return, ReturnItem
from orderApp.schemas import (
    OrderOut, OrderIn, OrderItemOut,
    OrderStatusIn, ReturnOut, ReturnIn, ReturnItemOut, ReturnItemIn, OrderCancellationIn
)
from productApp.models import Product, Stock
from warehouseApp.models import Warehouse
import qrcode
from io import BytesIO
from django.core.files import File
from ninja.errors import HttpError
from django.db import transaction

order_router = Router(tags=['Заказы'])

@order_router.post('/order_create', response=OrderOut)
def create_order(request, data: OrderIn):
    warehouse = get_object_or_404(Warehouse, id=data.warehouse_id)

    # Проверка наличия и достаточности запаса
    for item in data.items:
        product = get_object_or_404(Product, id=item.product_id)
        stock = get_object_or_404(Stock, product=product, warehouse=warehouse)
        if stock.quantity < item.quantity:
            raise HttpError(400,
                            f"Недостаточно товара '{product.name}' на складе '{warehouse.name}'")

    # Создание заказа и QR-кода
    with transaction.atomic():
        order = Order.objects.create(
            warehouse=warehouse,
            client_name=data.client_name,                 # NEW
            destination_address=data.destination_address, # NEW
            comment=data.comment                          # NEW
        )

        # Генерация QR
        qr_data = request.build_absolute_uri(f"/api/orders/order/{order.id}")
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill='black', back_color='white')
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        file_name = f"order_{order.id}_qr.png"
        order.qr_code.save(file_name, File(buffer), save=True)
        buffer.close()

        items_out = []
        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            stock = get_object_or_404(Stock, product=product, warehouse=warehouse)
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price                     # NEW: сохраняем цену продукта
            )
            stock.quantity -= item.quantity
            stock.save()
            items_out.append(OrderItemOut(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity,
                price=product.price                     # NEW
            ))

        return OrderOut(
            id=order.id,
            status=order.status,
            created_at=order.created_at.isoformat(),
            warehouse=order.warehouse.id,
            qr_code=order.qr_code.url if order.qr_code else None,
            client_name=order.client_name,                 # NEW
            destination_address=order.destination_address, # NEW
            comment=order.comment,                         # NEW
            total_price=order.total_price,                 # NEW
            items=items_out
        )

@order_router.get('/order/{order_id}', response=OrderOut)
def get_order(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    items_out = [
        OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity,
            price=item.price                    # NEW
        )
        for item in order.items.all()
    ]

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        client_name=order.client_name,                 # NEW
        destination_address=order.destination_address, # NEW
        comment=order.comment,                         # NEW
        total_price=order.total_price,                 # NEW
        items=items_out,
        cancellation_reason=order.cancellation_reason
    )

@order_router.get('/order', response=list[OrderOut])
def list_orders(request):
    orders = Order.objects.all().select_related('warehouse').prefetch_related('items__product')
    result = []

    for order in orders:
        items_out = [
            OrderItemOut(
                product_id=item.product.id,
                name=item.product.name,
                quantity=item.quantity,
                price=item.price              # NEW
            )
            for item in order.items.all()
        ]

        result.append(OrderOut(
            id=order.id,
            status=order.status,
            created_at=order.created_at.isoformat(),
            warehouse=order.warehouse.id,
            qr_code=order.qr_code.url if order.qr_code else None,
            client_name=order.client_name,                 # NEW
            destination_address=order.destination_address, # NEW
            comment=order.comment,                         # NEW
            total_price=order.total_price,                 # NEW
            items=items_out
        ))

    return result

@order_router.patch('/order/{order_id}/status', response=OrderOut)
def update_order_status(request, order_id: int, data: OrderStatusIn):
    order = get_object_or_404(Order, id=order_id)

    if data.status not in dict(Order.STATUS_CHOICES):
        raise HttpError(400, f"Недопустимый статус: {data.status}")

    order.status = data.status
    order.save()

    items_out = [
        OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity,
            price=item.price                # NEW
        )
        for item in order.items.all()
    ]

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        client_name=order.client_name,                 # NEW
        destination_address=order.destination_address, # NEW
        comment=order.comment,                         # NEW
        total_price=order.total_price,                 # NEW
        items=items_out,
        cancellation_reason=order.cancellation_reason
    )

@order_router.patch('/order/{order_id}/cancel', response=OrderOut)
def cancel_order(request, order_id: int, data: OrderCancellationIn):
    order = get_object_or_404(Order, id=order_id)

    if order.status == 'cancelled':
        raise HttpError(400, "Заказ уже отменен")

    order.status = 'cancelled'
    order.cancellation_reason = data.reason  # 🆕
    order.save()

    items_out = [
        OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity,
            price=item.price
        )
        for item in order.items.all()
    ]

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        client_name=order.client_name,
        destination_address=order.destination_address,
        comment=order.comment,
        cancellation_reason=order.cancellation_reason,  # 🆕
        total_price=order.total_price,
        items=items_out
    )
