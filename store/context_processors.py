def cart_summary(request):
    cart = request.session.get("cart", {})
    count = sum(int(v.get("quantity", 0)) for v in cart.values())
    return {"cart_count": count}
