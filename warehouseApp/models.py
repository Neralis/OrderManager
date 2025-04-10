from django.db import models

class Warehouse(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название склада"
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Адрес"
    )

    class Meta:
        verbose_name_plural = 'Warehouse (Склады)'

    def __str__(self):
        return self.name