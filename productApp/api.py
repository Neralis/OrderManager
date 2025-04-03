from ninja import Schema, Router
from productApp.models import Product
from typing import List
from productApp.schemas import ProductIn, ProductOut

# Роутер для всех эндпоинтов, относящихся к товарам
product_router = Router(tags=['Товары'])

@product_router.get('/products', response=List[ProductOut])
def get_products(request):
    products = Product.objects.all()
    return products

@product_router.post('/products', response=ProductOut)
def create_product(request, data: ProductIn):
    product = Product(
        name=data.name,
        product_type=data.product_type,
        price=data.price
    )
    product.save()
    return product