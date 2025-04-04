from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Coupon, CouponRestriction


class CouponRestrictionInline(admin.StackedInline):
    model = CouponRestriction
    filter_horizontal = ('products', 'categories', 'shops', 'user_groups')
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        'code', 
        'type', 
        'display_value', 
        'is_active', 
        'valid_period', 
        'usage_count', 
        'shop_name',
    )
    list_filter = ('is_active', 'type', 'shop')
    search_fields = ('code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CouponRestrictionInline]
    fieldsets = (
        (_('Coupon Information'), {
            'fields': ('code', 'description', 'is_active')
        }),
        (_('Discount Details'), {
            'fields': ('type', 'value', 'max_discount_amount')
        }),
        (_('Validity Period'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Ownership'), {
            'fields': ('created_by', 'shop')
        }),
        (_('System Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_value(self, obj):
        if obj.type == 'percentage':
            return f"{obj.value}%"
        elif obj.type == 'fixed':
            return f"${obj.value}"
        else:
            return obj.get_type_display()
    display_value.short_description = _("Value")
    
    def valid_period(self, obj):
        end_date = obj.end_date.strftime('%Y-%m-%d') if obj.end_date else '∞'
        return f"{obj.start_date.strftime('%Y-%m-%d')} - {end_date}"
    valid_period.short_description = _("Validity Period")
    
    def usage_count(self, obj):
        try:
            return f"{obj.restriction.usage_count} / {obj.restriction.usage_limit or '∞'}"
        except:
            return "0 / ∞"
    usage_count.short_description = _("Usage")
    
    def shop_name(self, obj):
        return obj.shop.name if obj.shop else _("Platform")
    shop_name.short_description = _("Owner")
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
