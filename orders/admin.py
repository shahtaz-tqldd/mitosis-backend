from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Order, OrderItem, ShippingAddress, PaymentInfo


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('final_price',)
    extra = 0
    fields = ('product', 'shop', 'quantity', 'base_price',)

    def base_price(self, obj):
        return obj.product.base_price
    base_price.short_description = _("Base Price")


class ShippingAddressInline(admin.StackedInline):
    model = ShippingAddress
    can_delete = False
    extra = 0


class PaymentInfoInline(admin.StackedInline):
    model = PaymentInfo
    can_delete = False
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name', 
        'subtotal', 
        'status', 
        'created_at', 
        'shop_count',
        'view_details',
    )
    list_filter = (
        'status', 
        'created_at', 
        'shops', 
        'payment__payment_method',
    )
    search_fields = (
        'order_number', 
        'user__email', 
        'user__first_name', 
        'user__last_name',
        'shipping_address__recipient_name',
    )
    readonly_fields = (
        'id', 
        'created_at', 
        'updated_at', 
        'completed_at',
        'subtotal',
    )
    fieldsets = (
        (_('Order Information'), {
            'fields': (
                'order_number', 
                'user', 
                'status', 
                'notes',
                'tracking_number',
            )
        }),
        (_('Financial Details'), {
            'fields': (
                'subtotal', 
                'tax_amount', 
                'shipping_cost', 
                'total_amount',
            )
        }),
        (_('Discounts Applied'), {
            'fields': ('coupon', 'campaigns'),
            'classes': ('collapse',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
        (_('Advanced'), {
            'fields': ('id', 'ip_address', 'shops'),
            'classes': ('collapse',),
        }),
    )
    inlines = [OrderItemInline, ShippingAddressInline, PaymentInfoInline]
    date_hierarchy = 'created_at'
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_completed']
    
    def customer_name(self, obj):
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.email})"
        try:
            return obj.shipping_address.recipient_name
        except:
            return _("Guest")
    customer_name.short_description = _("Customer")
    
    def shop_count(self, obj):
        return obj.shops.count()
    shop_count.short_description = _("Vendors")
    
    def view_details(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.id])
        return format_html('<a href="{}">View Details</a>', url)
    view_details.short_description = _("Details")
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Exclude cart status from main list view unless specific filter is applied
        if not request.GET.get('status__exact') == 'cart':
            queryset = queryset.exclude(status='cart')
        return queryset
    
    def save_model(self, request, obj, form, change):
        # Recalculate totals when saving from admin
        super().save_model(request, obj, form, change)
        obj.calculate_totals()
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = _("Mark selected orders as processing")
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = _("Mark selected orders as shipped")
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = _("Mark selected orders as delivered")
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed', completed_at=timezone.now())
    mark_as_completed.short_description = _("Mark selected orders as completed")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'order_number', 'quantity', 'base_price', 'final_price', 'shop_name')
    list_filter = ('shop',)
    search_fields = ('product__name', 'order__order_number')
    readonly_fields = ('final_price',)
    
    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = _("Product")
    
    def shop_name(self, obj):
        return obj.shop.name
    shop_name.short_description = _("Shop")
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = _("Order")


# Register the remaining models
@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'order_number', 'city', 'country', 'postal_code')
    search_fields = ('recipient_name', 'order__order_number', 'city', 'country')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = _("Order")


@admin.register(PaymentInfo)
class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'payment_method', 'amount', 'status', 'payment_date')
    list_filter = ('payment_method', 'status')
    search_fields = ('order__order_number', 'transaction_id')
    
    def order_number(self, obj):
        return obj.order.order_number
    order_number.short_description = _("Order")
