from django.shortcuts import get_object_or_404
from ninja import Router
from orderApp.models import Order, OrderItem, Return, ReturnItem
from orderApp.schemas import OrderOut, OrderIn, OrderItemOut, OrderStatusIn, ReturnOut, ReturnIn, ReturnItemOut, \
    ReturnItemIn
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
                            f"Insufficient stock for product {product.name} at warehouse {warehouse.name}: {stock.quantity} available, {item.quantity} requested")

    # Создание заказа в транзакции
    with transaction.atomic():
        order = Order.objects.create(
            warehouse=warehouse
        )

        # Генерация QR-кода
        qr_data = request.build_absolute_uri(f"/api/orders/order/{order.id}")
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill='black', back_color='white')

        # Сохранение QR-кода
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        file_name = f"order_{order.id}_qr.png"
        order.qr_code.save(file_name, File(buffer), save=True)
        buffer.close()

        items_out = []

        # Создание элементов заказа и уменьшение запаса
        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            stock = get_object_or_404(Stock, product=product, warehouse=warehouse)
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity
            )
            # Уменьшаем запас
            stock.quantity -= item.quantity
            stock.save()
            items_out.append(OrderItemOut(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity
            ))

        return OrderOut(
            id=order.id,
            status=order.status,
            created_at=order.created_at.isoformat(),
            warehouse=order.warehouse.id,
            qr_code=order.qr_code.url if order.qr_code else None,
            items=items_out
        )


@order_router.get('/order/{order_id}', response=OrderOut)
def get_order(request, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all()

    items_out = [
        OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity
        )
        for item in items
    ]

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        items=items_out
    )


@order_router.patch('/order/{order_id}/status', response=OrderOut)
def update_order_status(request, order_id: int, data: OrderStatusIn):
    order = get_object_or_404(Order, id=order_id)

    # Проверка допустимого статуса
    if data.status not in dict(Order.STATUS_CHOICES):
        raise HttpError(400, f"Invalid status. Must be one of: {', '.join([s[0] for s in Order.STATUS_CHOICES])}")

    # Обновление статуса
    order.status = data.status
    order.save()

    items_out = [
        OrderItemOut(
            product_id=item.product.id,
            name=item.product.name,
            quantity=item.quantity
        )
        for item in order.items.all()
    ]

    return OrderOut(
        id=order.id,
        status=order.status,
        created_at=order.created_at.isoformat(),
        warehouse=order.warehouse.id,
        qr_code=order.qr_code.url if order.qr_code else None,
        items=items_out
    )


@order_router.post('/order/{order_id}/return', response=ReturnOut)
def create_return(request, order_id: int, data: ReturnIn):
    order = get_object_or_404(Order, id=order_id)

    # Проверка, можно ли вернуть заказ
    if order.status not in ['new', 'processing', 'completed']:
        raise HttpError(400,
                        f"Order cannot be returned. Current status: {order.status}. Must be 'processing' or 'completed'.")

    # Проверка, существует ли возврат
    if Return.objects.filter(order=order).exists():
        raise HttpError(400, "Order already has a return.")

    # Проверка возвращаемых товаров
    order_items = {item.product.id: item.quantity for item in order.items.all()}
    total_returned_quantity = 0
    total_order_quantity = sum(order_items.values())

    for item in data.items:
        product_id = item.product_id
        return_quantity = item.quantity
        if product_id not in order_items:
            raise HttpError(400, f"Product ID {product_id} not found in order.")
        if return_quantity > order_items[product_id]:
            raise HttpError(400,
                            f"Return quantity {return_quantity} for product ID {product_id} exceeds ordered quantity {order_items[product_id]}.")
        total_returned_quantity += return_quantity

    # Создание возврата в транзакции
    with transaction.atomic():
        # Создание записи о возврате
        return_obj = Return.objects.create(
            order=order,
            reason=data.reason or ""
        )

        # Создание возвращаемых элементов и возврат запаса
        return_items_out = []
        for item in data.items:
            product = get_object_or_404(Product, id=item.product_id)
            stock = get_object_or_404(Stock, product=product, warehouse=order.warehouse)
            ReturnItem.objects.create(
                return_obj=return_obj,
                product=product,
                quantity=item.quantity
            )
            # Возврат запаса
            stock.quantity += item.quantity
            stock.save()
            return_items_out.append(ReturnItemOut(
                product_id=product.id,
                name=product.name,
                quantity=item.quantity
            ))

        # Обновление статуса заказа, если возвращены все товары
        if total_returned_quantity == total_order_quantity:
            order.status = 'returned'
            order.save()

    return ReturnOut(
        order_id=order.id,
        reason=return_obj.reason,
        created_at=return_obj.created_at.isoformat(),
        items=return_items_out
    )