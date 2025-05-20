from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from userApp.models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("middle_name",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("middle_name",)}),
    )

