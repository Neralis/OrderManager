from django.core.files.storage import default_storage
from django.db import models
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from ninja import Schema, Router, UploadedFile
from productApp.models import Product, Stock, ProductImage
from typing import List, Optional
from productApp.schemas import ProductIn, ProductOut, ProductImageOut, ProductImageIn
from warehouseApp.models import Warehouse

# Роутер для всех эндпоинтов, относящихся к товарам
product_router = Router(tags=['Товары'])

@product_router.get('/product_list_get', response=List[ProductOut])
def get_products(request):
    products = Product.objects.select_related("warehouse").all()

    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "product_type": p.product_type,
            "product_description": p.product_description,
            "price": p.price,
            "warehouse": p.warehouse.id
        })
    return result

@product_router.post('/product_create', response=ProductOut)
def create_product(request, data: ProductIn):
    warehouse = get_object_or_404(Warehouse, id=data.warehouse)

    product = Product.objects.create(
        name=data.name,
        product_type=data.product_type,
        price=data.price,
        warehouse=warehouse,  # без скобок!
        product_description=data.product_description,
    )
    return {
        "id": product.id,
        "name": product.name,
        "product_type": product.product_type,
        "product_description": product.product_description,
        "price": product.price,
        "warehouse": warehouse.id  # 👈 вернём только id
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
    # Находим продукт
    product = Product.objects.get(id=product_id)

    if warehouse_id is not None:
        # Если склад указан — получаем остаток на конкретном складе
        warehouse = Warehouse.objects.get(id=warehouse_id)
        stock = Stock.objects.filter(product=product, warehouse=warehouse).first()

        if stock:
            return {"product": product.name, "warehouse": warehouse.name, "quantity": stock.quantity}
        else:
            return {"detail": "Нет остатков на складе для данного продукта."}
    else:
        # Если склад не указан — получаем общее количество по всем складам
        total_quantity = Stock.objects.filter(product=product).aggregate(total=Sum('quantity'))["total"] or 0
        return {
            "product": product.name,
            "total_quantity_all_warehouses": total_quantity
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