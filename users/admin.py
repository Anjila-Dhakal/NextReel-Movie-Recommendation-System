from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_new_user', 'theme_preference')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_new_user', 'theme_preference')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('NextReel Profile', {'fields': ('bio', 'avatar', 'theme_preference', 'is_new_user')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('NextReel Profile', {'fields': ('bio', 'avatar', 'theme_preference')}),
    )
