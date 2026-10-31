from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    def __str__(self): return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=160)
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=12, blank=True)
    gstin = models.CharField(max_length=15, blank=True, help_text="Optional supplier GSTIN; validate before tax use.")
    website = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image_url = models.URLField(blank=True, help_text="Optional hosted product image URL")
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Track supplier availability or local stock.")
    active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    @property
    def estimated_margin(self):
        return self.selling_price - self.supplier_cost
    def __str__(self): return self.name

class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    def __str__(self): return self.code

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"), ("confirmed", "Confirmed"), ("supplier_ordered", "Supplier ordered"),
        ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled"),
        ("returned", "Returned"),
    ]
    PAYMENT_CHOICES = [("cod", "Cash on Delivery"), ("online", "Online payment")]
    PAYMENT_STATUS = [("unpaid", "Unpaid"), ("pending", "Payment pending"), ("paid", "Paid"), ("refunded", "Refunded")]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="store_orders")
    order_number = models.CharField(max_length=24, unique=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=12)
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES, default="cod")
    payment_status = models.CharField(max_length=12, choices=PAYMENT_STATUS, default="unpaid")
    gstin = models.CharField(max_length=15, blank=True, help_text="Optional customer GSTIN for eligible business invoices.")
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_reference = models.CharField(max_length=120, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=120, blank=True)
    customer_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=180)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    def line_total(self): return self.unit_price * self.quantity
    def __str__(self): return f"{self.product_name} x {self.quantity}"


class SupplierPurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"), ("sent", "Sent to supplier"),
        ("accepted", "Accepted"), ("shipped", "Shipped by supplier"),
        ("received", "Fulfilled"), ("cancelled", "Cancelled"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="supplier_purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    supplier_order_reference = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.order.order_number} → {self.supplier.name}"

class SupplierPurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(SupplierPurchaseOrder, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"{self.product.name} × {self.quantity}"
