from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.analytics_dashboard, name="dashboard"),
]

