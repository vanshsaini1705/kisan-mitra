from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html, mark_safe
from .models import User, Product


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {
            'fields': ('username', 'password'),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email'),
        }),
        ('KisanBazaar Profile', {
            'fields': ('role', 'phone', 'village'),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'phone', 'village'),
        }),
    )

    list_display    = ('username', 'email', 'role_badge', 'phone', 'village', 'is_active', 'date_joined')
    list_filter     = ('role', 'is_active', 'date_joined')
    search_fields   = ('username', 'email', 'phone', 'village', 'first_name', 'last_name')
    ordering        = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')

    @admin.display(description='Role')
    def role_badge(self, obj):
        color_map = {
            'farmer':     '#16a34a',
            'buyer':      '#2563eb',
            'warehouse':  '#7c3aed',
            'wholesaler': '#d97706',
        }
        color = color_map.get(obj.role, '#6b7280')
        label = obj.get_role_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            color,
            label,
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = (
        'crop_name', 'farmer', 'qty_display', 'price_display',
        'location', 'harvest_date', 'freshness_display', 'is_available', 'created_at',
    )
    list_filter         = ('is_available', 'harvest_date', 'location', 'farmer__role')
    search_fields       = ('crop_name', 'farmer__username', 'farmer__phone', 'location')
    readonly_fields     = ('created_at', 'updated_at', 'expiry_date')   # expiry_date is auto-set
    date_hierarchy      = 'harvest_date'
    list_per_page       = 50
    list_select_related = ('farmer',)

    @admin.display(description='Quantity')
    def qty_display(self, obj):
        return format_html('{} kg', obj.quantity)

    @admin.display(description='Price / kg')
    def price_display(self, obj):
        return format_html('₹{}', obj.price)

    @admin.display(description='Freshness')
    def freshness_display(self, obj):
        days = obj.days_until_spoilage
        if days <= 0:
            return mark_safe('<span style="color:#6b7280;font-weight:700;">Expired</span>')
        if days <= 2:
            return format_html(
                '<span style="color:#dc2626;font-weight:700;">{} days ⚠️</span>',
                days,
            )
        if days <= 4:
            return format_html(
                '<span style="color:#d97706;font-weight:700;">{} days</span>',
                days,
            )
        return format_html(
            '<span style="color:#16a34a;font-weight:700;">{} days ✅</span>',
            days,
        )