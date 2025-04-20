from django.db import models

from warehouseApp.models import Warehouse


class Product(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название товара"
    )
    product_type = models.CharField(
        max_length=100,
        verbose_name="Вид товара"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена"
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name="products",
        null=True,
        blank=True,
    )
    product_description = models.CharField(
        max_length=255,
        verbose_name="Описание товара",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = 'Product (Товары)'

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        upload_to='product_images/'
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.product.name} Image"


class Stock(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stocks'
    )
    quantity = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        unique_together = ('product', 'warehouse')  # Уникальное сочетание продукта и склада

    def __str__(self):
        return f"{self.product.name} на складе {self.warehouse.name}: {self.quantity} шт."