from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Campaign, CampaignPromoCode, CampaignTracking


class CampaignPromoCodeInline(admin.TabularInline):
    model = CampaignPromoCode
    extra = 1


class CampaignTrackingInline(admin.TabularInline):
    model = CampaignTracking
    readonly_fields = ('date', 'orders', 'revenue', 'discount_total', 'views', 'conversions')
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'campaign_type', 
        'discount_display', 
        'active_status', 
        'date_range', 
        'items_count', 
        'priority'
    )
    list_filter = ('is_active', 'campaign_type', 'is_public')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('categories', 'products', 'shops')
    inlines = [CampaignPromoCodeInline, CampaignTrackingInline]
    fieldsets = (
        (_('Campaign Information'), {
            'fields': ('name', 'slug', 'description', 'banner_image')
        }),
        (_('Discount Details'), {
            'fields': ('campaign_type', 'discount_value', 'is_percentage')
        }),
        (_('Validity & Display'), {
            'fields': ('is_active', 'start_date', 'end_date', 'is_public', 'priority')
        }),
        (_('Targeting'), {
            'fields': ('categories', 'products', 'shops')
        }),
        (_('Purchase Requirements'), {
            'fields': ('min_purchase_amount', 'min_purchase_items'),
            'classes': ('collapse',)
        }),
        (_('System Information'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    date_hierarchy = 'start_date'
    
    def discount_display(self, obj):
        if obj.is_percentage:
            return f"{obj.discount_value}%"
        else:
            return f"${obj.discount_value}"
    discount_display.short_description = _("Discount")
    
    def active_status(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return _("Inactive")
        elif now < obj.start_date:
            return _("Scheduled")
        elif now > obj.end_date:
            return _("Expired")
        else:
            return _("Active")
    active_status.short_description = _("Status")
    
    def date_range(self, obj):
        return f"{obj.start_date.strftime('%Y-%m-%d')} - {obj.end_date.strftime('%Y-%m-%d')}"
    date_range.short_description = _("Period")
    
    def items_count(self, obj):
        target_counts = []
        
        if obj.products.exists():
            target_counts.append(f"{obj.products.count()} products")
        if obj.categories.exists():
            target_counts.append(f"{obj.categories.count()} categories")
        if obj.shops.exists():
            target_counts.append(f"{obj.shops.count()} shops")
            
        if not target_counts:
            if obj.campaign_type == 'site_wide':
                return _("All products")
            else:
                return "-"
                
        return ", ".join(target_counts)
    items_count.short_description = _("Targets")
    
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CampaignPromoCode)
class CampaignPromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'campaign', 'is_active', 'usage_status')
    list_filter = ('is_active', 'campaign')
    search_fields = ('code', 'campaign__name')
    
    def usage_status(self, obj):
        if obj.usage_limit == 0:
            return f"{obj.usage_count} / ∞"
        return f"{obj.usage_count} / {obj.usage_limit}"
    usage_status.short_description = _("Usage")


@admin.register(CampaignTracking)
class CampaignTrackingAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'date', 'views', 'conversions', 'orders', 'revenue', 'discount_total', 'conversion_rate')
    list_filter = ('campaign', 'date')
    date_hierarchy = 'date'
    readonly_fields = ('conversion_rate',)
    
    def conversion_rate(self, obj):
        if obj.views > 0:
            rate = (obj.conversions / obj.views) * 100
            return f"{rate:.2f}%"
        return "0.00%"
    conversion_rate.short_description = _("Conversion Rate")


