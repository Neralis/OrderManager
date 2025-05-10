from ninja import Router
from django.http import FileResponse, HttpRequest
from reportApp.utils import export_filtered_orders_to_xlsx, export_stock_to_xlsx, export_single_order_to_xlsx

report_router = Router(tags=["Отчеты"])

@report_router.get("/orders_report")
def orders_report(request):
    return export_filtered_orders_to_xlsx(request)

@report_router.get("/stock_report")
def stock_report(request):
    return export_stock_to_xlsx(request)

@report_router.get("/order-report/{order_id}")
def single_order_report(request: HttpRequest, order_id: int):
    return export_single_order_to_xlsx(request, order_id)