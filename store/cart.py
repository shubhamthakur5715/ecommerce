from decimal import Decimal
from .models import Product

def get_cart_items(request):
    cart = request.session.get("cart", {})
    items, subtotal = [], Decimal("0.00")
    for key, entry in cart.items():
        try:
            product = Product.objects.get(pk=int(key), active=True)
            quantity = max(1, min(int(entry.get("quantity", 1)), 99))
            line_total = product.selling_price * quantity
            items.append({"product": product, "quantity": quantity, "line_total": line_total})
            subtotal += line_total
        except (Product.DoesNotExist, ValueError, TypeError):
            continue
    return items, subtotal
