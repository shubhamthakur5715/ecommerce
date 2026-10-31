import uuid
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .models import Category, Product, Order, OrderItem
from .forms import SignUpForm, CheckoutForm
from .cart import get_cart_items

def home(request):
    featured = Product.objects.filter(active=True, featured=True).select_related("category")[:8]
    if not featured.exists():
        featured = Product.objects.filter(active=True).select_related("category")[:8]
    return render(request, "store/home.html", {"products": featured, "categories": Category.objects.all()})

def product_list(request):
    products = Product.objects.filter(active=True).select_related("category")
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    sort = request.GET.get("sort", "")
    if q: products = products.filter(name__icontains=q) | products.filter(description__icontains=q)
    if category:
        products = products.filter(category__slug=category)
    if sort == "price_low": products = products.order_by("selling_price")
    elif sort == "price_high": products = products.order_by("-selling_price")
    return render(request, "store/product_list.html", {"products": products.distinct(), "categories": Category.objects.all(), "q": q, "selected_category": category, "sort": sort})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    return render(request, "store/product_detail.html", {"product": product})

def cart_view(request):
    items, subtotal = get_cart_items(request)
    return render(request, "store/cart.html", {"items": items, "subtotal": subtotal})

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, active=True)
    cart = request.session.get("cart", {})
    key = str(product.id)
    current = int(cart.get(key, {}).get("quantity", 0))
    cart[key] = {"quantity": min(current + max(1, int(request.POST.get("quantity", 1))), 99)}
    request.session["cart"] = cart
    messages.success(request, f"{product.name} added to your cart.")
    return redirect(request.POST.get("next") or "cart")

@require_POST
def update_cart(request, product_id):
    cart = request.session.get("cart", {})
    key = str(product_id)
    try: quantity = int(request.POST.get("quantity", 1))
    except ValueError: quantity = 1
    if quantity <= 0: cart.pop(key, None)
    elif key in cart: cart[key]["quantity"] = min(quantity, 99)
    request.session["cart"] = cart
    return redirect("cart")

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else: form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

@login_required
def checkout(request):
    items, subtotal = get_cart_items(request)
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("product_list")
    initial = {"full_name": request.user.get_full_name() or request.user.username, "email": request.user.email}
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            shipping = Decimal("0.00") if subtotal >= Decimal("999.00") else Decimal("79.00")
            # Online payment is not considered paid until a verified gateway callback is implemented.
            pay_status = "unpaid" if data["payment_method"] == "cod" else "pending"
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user, order_number="DS" + uuid.uuid4().hex[:10].upper(),
                    full_name=data["full_name"], email=data["email"], phone=data["phone"],
                    address=data["address"], city=data["city"], state=data["state"],
                    postal_code=data["postal_code"], gstin=data.get("gstin", "").strip().upper(), payment_method=data["payment_method"],
                    payment_status=pay_status, subtotal=subtotal, shipping_fee=shipping,
                    discount=Decimal("0.00"), total=subtotal + shipping, customer_note=data["customer_note"])
                for item in items:
                    OrderItem.objects.create(order=order, product=item["product"],
                        product_name=item["product"].name, unit_price=item["product"].selling_price,
                        quantity=item["quantity"])
            request.session["cart"] = {}
            if order.payment_method == "online":
                return redirect("pay_order", order_number=order.order_number)
            return redirect("order_success", order_number=order.order_number)
    else: form = CheckoutForm(initial=initial)
    return render(request, "store/checkout.html", {"form": form, "items": items, "subtotal": subtotal})

@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, "store/order_success.html", {"order": order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/my_orders.html", {"orders": orders})


@login_required
def pay_order(request, order_number):
    from django.conf import settings
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.payment_method != "online":
        return redirect("order_success", order_number=order.order_number)
    if order.payment_status == "paid":
        return redirect("order_success", order_number=order.order_number)
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, "Online payments are not configured yet. Set Razorpay test keys in your .env file.")
        return render(request, "store/payment_unconfigured.html", {"order": order})
    return render(request, "store/payment.html", {"order": order, "razorpay_key_id": settings.RAZORPAY_KEY_ID})

@login_required
@require_POST
def create_razorpay_order(request, order_number):
    import razorpay
    from django.conf import settings
    from django.http import JsonResponse
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.payment_method != "online" or order.payment_status == "paid":
        return JsonResponse({"error": "This order is not payable."}, status=400)
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({"error": "Payment gateway is not configured."}, status=503)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    try:
        payment_order = client.order.create({
            "amount": int(order.total * 100),
            "currency": "INR",
            "receipt": order.order_number,
            "notes": {"store_order_number": order.order_number},
        })
        order.razorpay_order_id = payment_order["id"]
        order.payment_status = "pending"
        order.save(update_fields=["razorpay_order_id", "payment_status"])
        return JsonResponse({"id": payment_order["id"], "amount": payment_order["amount"], "currency": payment_order["currency"], "key": settings.RAZORPAY_KEY_ID, "name": "DropNest", "description": "Order " + order.order_number, "prefill": {"name": order.full_name, "email": order.email, "contact": order.phone}})
    except Exception:
        return JsonResponse({"error": "Could not create payment session. Please try again."}, status=502)

@login_required
@require_POST
def verify_razorpay_payment(request, order_number):
    import json
    import razorpay
    from django.conf import settings
    from django.http import JsonResponse
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    try:
        payload = json.loads(request.body.decode("utf-8"))
        payment_id = payload.get("razorpay_payment_id", "")
        payment_order_id = payload.get("razorpay_order_id", "")
        signature = payload.get("razorpay_signature", "")
        if not order.razorpay_order_id or payment_order_id != order.razorpay_order_id:
            return JsonResponse({"error": "Payment order does not match."}, status=400)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        client.utility.verify_payment_signature({
            "razorpay_order_id": payment_order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        order.razorpay_payment_id = payment_id
        order.payment_status = "paid"
        order.status = "confirmed"
        order.save(update_fields=["razorpay_payment_id", "payment_status", "status"])
        return JsonResponse({"ok": True, "redirect_url": "/orders/success/" + order.order_number + "/"})
    except Exception:
        return JsonResponse({"error": "Payment verification failed. Contact support if money was deducted."}, status=400)
