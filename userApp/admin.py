from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from userApp.models import CustomUser
from unfold.admin import ModelAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("middle_name",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительно", {"fields": ("middle_name",)}),
    )

