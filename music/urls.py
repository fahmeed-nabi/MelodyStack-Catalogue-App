from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name='login'),
    path("/anonymous", views.anonymous_front, name="anonymous_front")
]
