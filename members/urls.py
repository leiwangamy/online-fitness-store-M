from django.urls import path
from . import views

app_name = "members"

urlpatterns = [
    path("membership/", views.membership_plans, name="membership_plans"),
    path("membership/my/", views.my_membership, name="my_membership"),
]
