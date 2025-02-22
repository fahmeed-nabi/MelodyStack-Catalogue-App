from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name='login'),
<<<<<<< HEAD
    path("public-collections/", views.anonymous_front, name="public")
    # path('librarian/<str:pk>/', views.librarian_page, name='librarian'),
    # path('patron/<str:pk>/', views.patron_page, name='patron'),
=======
    path("public-collections/", views.anonymous_front, name="anon"),
    path('librarian/', views.librarian_page, name='librarian'),
    path('patron/', views.patron_page, name='patron'),
    path('redir', views.redir, name="redir"),
    path("logout", views.logout_view, name="logout_view"),
>>>>>>> 0f78ed45767210f5f9298f527f8bb04e18c6ecab
]
