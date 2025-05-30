from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    middle_name = models.CharField("Отчество", max_length=150, blank=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
