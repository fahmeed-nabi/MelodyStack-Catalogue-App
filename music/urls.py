from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_page, name='login'),
    path('librarian/<str:pk>', views.librarian_page, name='librarian'),
    path('patron/<str:pk>', views.patron_page, name='patron'),
]
