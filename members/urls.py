from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),  # /
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
     # cart
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/remove/<int:pk>/", views.remove_from_cart, name="remove_from_cart"),

    # payment / checkout (login required in view)
    path("payment/", views.payment, name="payment"),
]