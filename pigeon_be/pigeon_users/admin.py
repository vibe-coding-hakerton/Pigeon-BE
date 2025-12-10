from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 사용자 관리자"""

    list_display = [
        'username',
        'email',
        'gender',
        'birth_date',
        'phone_number',
        'is_active',
        'date_joined',
    ]
    list_filter = ['is_active', 'is_staff', 'gender']
    search_fields = ['username', 'email', 'phone_number']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('추가 정보', {
            'fields': ('gender', 'birth_date', 'phone_number'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('추가 정보', {
            'fields': ('gender', 'birth_date', 'phone_number'),
        }),
    )
