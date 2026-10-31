from django.contrib import admin
from .models import Category, Supplier, Product, Coupon, Order, OrderItem, SupplierPurchaseOrder, SupplierPurchaseOrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "active")
    list_filter = ("active",)
    search_fields = ("name", "email")

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "selling_price", "supplier_cost", "stock_quantity", "active", "featured")
    list_filter = ("active", "featured", "category", "supplier")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_percent", "active", "valid_until")
    list_filter = ("active",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "full_name", "total", "status", "payment_method", "payment_status", "created_at")
    list_filter = ("status", "payment_method", "payment_status", "created_at")
    search_fields = ("order_number", "full_name", "email", "phone", "tracking_number")
    readonly_fields = ("order_number", "user", "subtotal", "shipping_fee", "discount", "total", "created_at")
    inlines = [OrderItemInline]


class SupplierPurchaseOrderItemInline(admin.TabularInline):
    model = SupplierPurchaseOrderItem
    extra = 1

@admin.register(SupplierPurchaseOrder)
class SupplierPurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "supplier", "status", "supplier_order_reference", "created_at")
    list_filter = ("status", "supplier", "created_at")
    search_fields = ("order__order_number", "supplier__name", "supplier_order_reference")
    inlines = [SupplierPurchaseOrderItemInline]
