from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name='login'),
    path("public-collections/", views.anonymous_front, name="anon"),
    path('librarian/', views.librarian_page, name='librarian'),
    path('patron/', views.patron_page, name='patron'),
    path('redir', views.redir, name="redir"),
    path("logout", views.logout_view, name="logout_view"),
]
