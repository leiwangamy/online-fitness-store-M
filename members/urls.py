from django.urls import path
from . import views

app_name = "members"

urlpatterns = [
    path("membership/", views.membership_plans, name="membership_plans"),
    path("membership/seller/", views.seller_membership_plans, name="seller_membership_plans"),
    path("membership/my/", views.my_membership, name="my_membership"),
    path("membership/subscriptions/", views.my_subscriptions, name="my_subscriptions"),
    path("membership/manage/", views.manage_subscription, name="manage_subscription"),
]
