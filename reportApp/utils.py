from datetime import datetime
from io import BytesIO

import openpyxl
import qrcode
from django.utils.dateparse import parse_date
from openpyxl.styles import Font, PatternFill
from django.http import HttpResponse
from orderApp.models import Order, OrderItem
from productApp.models import Stock
from openpyxl.drawing.image import Image as OpenpyxlImage


def export_filtered_orders_to_xlsx(request):
    start_raw = request.GET.get("start")
    end_raw = request.GET.get("end")

    start = parse_date(start_raw) if start_raw else None
    end = parse_date(end_raw) if end_raw else None

    # Далее фильтрация заказов
    orders = Order.objects.all()
    if start:
        orders = orders.filter(created_at__date__gte=start)
    if end:
        orders = orders.filter(created_at__date__lte=end)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Заказы"

    headers = ["ID заказа", "Статус", "Склад", "Дата создания", "Продукт", "Количество"]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True)

    # Цвета по статусам
    status_colors = {
        "new": "FFFACD",         # light yellow
        "processing": "ADD8E6",  # light blue
        "completed": "90EE90",   # light green
        "returned": "FFB6C1",    # light pink
    }

    for order in orders.prefetch_related('items__product'):
        for item in order.items.all():
            sheet.append([
                order.id,
                order.status,
                order.warehouse.name,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                item.product.name,
                item.quantity
            ])
            # Цветовая заливка для ячейки со статусом
            last_row = sheet.max_row
            status_cell = sheet.cell(row=last_row, column=2)
            color = status_colors.get(order.status)
            if color:
                status_cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f"attachment; filename=orders_report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    workbook.save(response)
    return response


def export_stock_to_xlsx(request):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Остатки товаров"

    headers = ["Склад", "Продукт", "Остаток"]
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    stocks = Stock.objects.select_related("warehouse", "product").order_by("warehouse__name", "product__name")

    for stock in stocks:
        sheet.append([
            stock.warehouse.name,
            stock.product.name,
            stock.quantity
        ])

    # Автоширина колонок
    for col in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in col)
        col_letter = col[0].column_letter
        sheet.column_dimensions[col_letter].width = max_length + 2

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    filename = f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response["Content-Disposition"] = f"attachment; filename={filename}"
    workbook.save(response)
    return response

def export_single_order_to_xlsx(request, order_id: int):
    order = Order.objects.prefetch_related('items__product').select_related('warehouse').get(id=order_id)

    # Создание Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Заказ {order.id}"

    # Заголовки
    headers = ["ID заказа", "Статус", "Склад", "Дата создания", "Продукт", "Количество"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Добавление строк заказа
    for item in order.items.all():
        ws.append([
            order.id,
            order.status,
            order.warehouse.name if order.warehouse else "—",
            order.created_at.strftime("%Y-%m-%d %H:%M"),
            item.product.name,
            item.quantity
        ])

    # Генерация QR-кода
    qr_data = f"Order ID: {order.id}\nStatus: {order.status}\nCreated: {order.created_at.strftime('%Y-%m-%d %H:%M')}"
    qr_img = qrcode.make(qr_data)

    img_io = BytesIO()
    qr_img.save(img_io, format='PNG')
    img_io.seek(0)

    img = OpenpyxlImage(img_io)
    img.width = 150
    img.height = 150

    # Вставка QR-кода ниже данных
    last_row = ws.max_row + 2
    img_anchor = f"A{last_row}"
    ws.add_image(img, img_anchor)

    # Сохраняем файл и отправляем
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f"attachment; filename=order_{order.id}_report.xlsx"
    wb.save(response)
    return response