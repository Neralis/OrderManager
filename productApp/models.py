from django.db import models

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

    class Meta:
        verbose_name_plural = 'Product (Товары)'

    def __str__(self):
        return self.name