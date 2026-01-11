from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("contact/", views.contact_page, name="contact"),
    path("blog/", views.blog_page, name="blog"),
    path("blog/<slug:slug>/", views.blog_detail, name="blog_detail"),
]

