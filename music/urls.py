from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name='login'),
    path("collections/", views.AnonymousFrontView.as_view(), name='collections'),
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('librarian/', views.librarian_page, name='librarian'),
    path('patron/', views.patron_page, name='patron'),
    path('redir', views.redir, name="redir"),
    path("logout", views.logout_view, name="logout_view"),
    path('patron/settings/', views.patron_settings_view, name='patron_settings'),
    path('librarian/settings/', views.librarian_settings_view, name='librarian_settings'),
    path('librarian/create_collection_item/', views.create_collection_item, name='create_collection_item'),
]

