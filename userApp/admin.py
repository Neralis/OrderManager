from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
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


admin.site.unregister(Group)


@admin.register(Group)
class CustomGroupAdmin(ModelAdmin):
    list_display = ["name", "pk", "get_permissions"]
    search_fields = ["name"]

    def get_permissions(self, obj):

        return ", ".join([perm.name for perm in obj.permissions.all()])

    get_permissions.short_description = "Права"