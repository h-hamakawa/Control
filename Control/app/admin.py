from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Category, CreditCard, Transaction, Debt, CalendarEvent


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('個人情報', {'fields': ('name',)}),
        ('権限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions',)


admin.register(UserProfile)(admin.ModelAdmin)
admin.register(Category)(admin.ModelAdmin)
admin.register(CreditCard)(admin.ModelAdmin)
admin.register(Transaction)(admin.ModelAdmin)
admin.register(Debt)(admin.ModelAdmin)
admin.register(CalendarEvent)(admin.ModelAdmin)
