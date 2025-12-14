from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from .cart import Cart
from products.models import Product  # adjust if needed

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)

    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override') == 'True'

    cart.add(product=product, quantity=quantity, override_quantity=override)
    return redirect('cart_detail')
