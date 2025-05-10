from django.db import models
from warehouseApp.models import Warehouse
from productApp.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    warehouse = models.ForeignKey('warehouseApp.Warehouse', on_delete=models.CASCADE)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)

    @property
    def total_price(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def __str__(self):
        return f"Order #{self.id} ({self.get_status_display()})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('productApp.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Return(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='related_return')
    reason = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return for Order {self.order.id}"

class ReturnItem(models.Model):
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Return {self.quantity} of {self.product.name} for Order {self.return_obj.order.id}"