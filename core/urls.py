from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI
from productApp.api import product_router
from userApp.api import auth_router
from warehouseApp.api import warehouse_router
from ninja_jwt.authentication import JWTAuth


api = NinjaAPI(
    title="API Системы управления складами и заказами",
    version="1.0.0",
    # auth=JWTAuth(),  # ⬅️ защищает все роуты по умолчанию (можно и роутер отдельно)
    openapi_extra={
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [{"BearerAuth": []}]  # ⬅️ добавит поле в Swagger UI
    }
)

api.add_router('/products/', product_router)
api.add_router('/warehouses/', warehouse_router)
api.add_router('/auth/', auth_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
