from django.core.files.storage import default_storage
from django.db import models
from django.shortcuts import get_object_or_404
from ninja import Schema, Router, UploadedFile
from ninja.errors import HttpError
from productApp.models import Product, Stock, ProductImage
from typing import List, Optional
from productApp.schemas import ProductIn, ProductOut, ProductImageOut, ProductImageIn, ProductUpdate
from warehouseApp.models import Warehouse
from userApp.utils import group_required

# Роутер для всех эндпоинтов, относящихся к товарам
product_router = Router(tags=['Товары'])


@product_router.get('/product_list_get', response=List[ProductOut])
#@group_required("admin")
def get_products(request, warehouse_id: Optional[int] = None):
    if warehouse_id:
        products = Product.objects.filter(stocks__warehouse_id=warehouse_id).distinct()
    else:
        products = Product.objects.all()

    result = []
    for p in products:
        stock_warehouses = Stock.objects.filter(product=p, quantity__gt=0).values_list('warehouse_id', flat=True)
        result.append({
            "id": p.id,
            "name": p.name,
            "product_type": p.product_type,
            "product_description": p.product_description,
            "price": p.price,
            # "warehouse": p.warehouse.id,
            "warehouses_with_stock": list(stock_warehouses)
        })
    return result


@product_router.get('/product_detail_get', response=ProductOut)
def get_product_detail(request, product_id: int, warehouse_id: Optional[int] = None):
    product = get_object_or_404(Product, id=product_id)

    current_warehouse = None
    current_quantity = None

    if warehouse_id is not None:
        stock = Stock.objects.filter(product=product, warehouse_id=warehouse_id).first()
        if not stock or stock.quantity <= 0:
            raise HttpError(404, "Товар не найден на указанном складе")
        current_warehouse = warehouse_id
        current_quantity = stock.quantity

    stock_warehouses = Stock.objects.filter(product=product, quantity__gt=0).values_list('warehouse_id', flat=True)

    return {
        "id": product.id,
        "name": product.name,
        "product_type": product.product_type,
        "product_description": product.product_description,
        "price": product.price,
        "current_warehouse": current_warehouse,
        "current_quantity": current_quantity,
        "warehouses_with_stock": list(stock_warehouses)
    }


@product_router.post('/product_create', response=ProductOut)
def create_product(request, data: ProductIn):

    product = Product.objects.create(
        name=data.name,
        product_type=data.product_type,
        price=data.price,
        # warehouse=warehouse,  # без скобок!
        product_description=data.product_description,
    )
    return {
        "id": product.id,
        "name": product.name,
        "product_type": product.product_type,
        "product_description": product.product_description,
        "price": product.price,
        # "warehouse": warehouse.id,  # 👈 вернём только id
        "warehouses_with_stock": []
    }

@product_router.patch('/product_update/{product_id}', response=ProductOut)
def update_product_partial(request, product_id: int, data: ProductUpdate):
    product = get_object_or_404(Product, id=product_id)

    if data.name is not None:
        product.name = data.name
    if data.product_type is not None:
        product.product_type = data.product_type
    if data.product_description is not None:
        product.product_description = data.product_description
    if data.price is not None:
        product.price = data.price

    product.save()

    # добавляем warehouses_with_stock
    stock_warehouses = Stock.objects.filter(product=product, quantity__gt=0).values_list('warehouse_id', flat=True)

    return {
        "id": product.id,
        "name": product.name,
        "product_type": product.product_type,
        "product_description": product.product_description,
        "price": product.price,
        "warehouses_with_stock": list(stock_warehouses)
    }

@product_router.delete("/product_delete")
def delete_product(request, product_id: int):
    try:
        # Находим товар
        product = Product.objects.get(id=product_id)

        # Проверяем, есть ли остатки на складах
        total_quantity = Stock.objects.filter(product=product).aggregate(total=models.Sum('quantity'))["total"] or 0

        if total_quantity > 0:
            return {
                "status": "error",
                "message": f"Невозможно удалить товар '{product.name}', пока на складах остаётся {total_quantity} шт. Расходуй весь товар перед удалением."
            }

        # Удаляем все записи об остатках (если они есть с нулевым количеством — на всякий случай)
        Stock.objects.filter(product=product).delete()

        # Удаляем сам товар
        product.delete()

        return {"status": "success", "message": f"Товар '{product.name}' успешно удалён"}

    except Product.DoesNotExist:
        return {"status": "error", "message": "Товар не найден"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@product_router.get('/product_stock')
def get_product_stock(request, product_id: int, warehouse_id: Optional[int] = None):
    product = Product.objects.get(id=product_id)

    if warehouse_id is not None:
        warehouse = Warehouse.objects.get(id=warehouse_id)
        stock = Stock.objects.filter(product=product, warehouse=warehouse).first()

        if stock:
            return {
                "product": product.name,
                # "warehouse": warehouse.name,
                "quantity": stock.quantity,
                "warehouses_with_stock": [warehouse.id]
            }
        else:
            return {"detail": "Нет остатков на складе для данного продукта."}
    else:
        stocks = Stock.objects.filter(product=product, quantity__gt=0)
        total_quantity = sum(stock.quantity for stock in stocks)
        warehouse_ids = [stock.warehouse.id for stock in stocks]

        return {
            "product": product.name,
            "total_quantity_all_warehouses": total_quantity,
            "warehouses_with_stock": warehouse_ids
        }



# Эндпоинт для добавления товара на склад


@product_router.post("/products/product_stock_add")
def add_product_stock(request, product_id: int, warehouse_id: int, quantity: int):
    try:
        # Получаем продукт и склад
        product = Product.objects.get(id=product_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)

        # Получаем или создаем запись на складе
        stock, created = Stock.objects.get_or_create(product=product, warehouse=warehouse)

        # Если запись была создана, необходимо указать начальное количество
        if created:
            stock.quantity = quantity
        else:
            # Если запись уже существует, обновляем количество
            stock.quantity += quantity

        stock.save()
        return {"status": "success", "stock_quantity": stock.quantity}
    except Product.DoesNotExist:
        return {"status": "error", "message": "Product not found"}
    except Warehouse.DoesNotExist:
        return {"status": "error", "message": "Warehouse not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@product_router.post("/products/product_stock_decrease")
def remove_product_stock(request, product_id: int, warehouse_id: int, quantity: int):
    try:
        # Получаем продукт и склад
        product = Product.objects.get(id=product_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)

        # Получаем запись об остатках
        stock = Stock.objects.filter(product=product, warehouse=warehouse).first()

        if not stock:
            return {"status": "error", "message": "Остаток на складе не найден"}

        # Проверка на достаточное количество
        if stock.quantity < quantity:
            return {
                "status": "error",
                "message": f"Недостаточно товара на складе. Доступно: {stock.quantity}"
            }

        # Уменьшаем количество
        stock.quantity -= quantity
        stock.save()

        return {"status": "success", "stock_quantity": stock.quantity}

    except Product.DoesNotExist:
        return {"status": "error", "message": "Продукт не найден"}
    except Warehouse.DoesNotExist:
        return {"status": "error", "message": "Склад не найден"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@product_router.post("/products/product_stock_transfer")
def transfer_product_stock(
    request,
    product_id: int,
    from_warehouse_id: int,
    to_warehouse_id: int,
    quantity: int
):
    try:
        # Получаем продукт и склады
        product = Product.objects.get(id=product_id)
        from_warehouse = Warehouse.objects.get(id=from_warehouse_id)
        to_warehouse = Warehouse.objects.get(id=to_warehouse_id)

        if from_warehouse_id == to_warehouse_id:
            return {"status": "error", "message": "Нельзя переместить товар на тот же склад"}

        # Остаток на складе-источнике
        from_stock = Stock.objects.filter(product=product, warehouse=from_warehouse).first()
        if not from_stock or from_stock.quantity < quantity:
            return {
                "status": "error",
                "message": f"Недостаточно товара на складе-источнике. Доступно: {from_stock.quantity if from_stock else 0}"
            }

        # Получаем или создаем запись на складе-назначении
        to_stock, _ = Stock.objects.get_or_create(product=product, warehouse=to_warehouse)

        # Выполняем перенос
        from_stock.quantity -= quantity
        to_stock.quantity += quantity

        from_stock.save()
        to_stock.save()

        return {
            "status": "success",
            "message": f"Перемещено {quantity} единиц товара",
            "from_warehouse_stock": from_stock.quantity,
            "to_warehouse_stock": to_stock.quantity
        }

    except Product.DoesNotExist:
        return {"status": "error", "message": "Продукт не найден"}
    except Warehouse.DoesNotExist:
        return {"status": "error", "message": "Склад не найден"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@product_router.post('/product/upload_image', response={200: ProductImageOut, 404: dict})
def upload_product_image(request, data: ProductImageIn, file: UploadedFile):
    try:
        product = Product.objects.get(id=data.product_id)

        # Сохраняем файл
        file_path = default_storage.save(f"product_images/{file.name}", file)

        # Создаем объект ProductImage
        image = ProductImage.objects.create(
            product=product,
            image=file_path,
            alt_text=data.alt_text or ""
        )

        return {
            "id": image.id,
            "product": product.id,
            "image_url": request.build_absolute_uri(image.image.url),
            "alt_text": image.alt_text,
            "uploaded_at": image.uploaded_at.isoformat()
        }

    except Product.DoesNotExist:
        return 404, {"message": "Товар не найден"}

@product_router.get('/product/images', response=List[ProductImageOut])
def get_product_images(request, product_id: int):
    images = ProductImage.objects.filter(product_id=product_id)
    return [
        {
            "id": img.id,
            "product": img.product.id,
            "image_url": request.build_absolute_uri(img.image.url),
            "alt_text": img.alt_text,
            "uploaded_at": img.uploaded_at.isoformat()
        }
        for img in images
    ]