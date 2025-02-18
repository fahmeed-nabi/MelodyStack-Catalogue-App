from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name='login'),
    path("public-collections/", views.anonymous_front.as_view(), name="anon")
    # path('librarian/<str:pk>/', views.librarian_page, name='librarian'),
    # path('patron/<str:pk>/', views.patron_page, name='patron'),
]
