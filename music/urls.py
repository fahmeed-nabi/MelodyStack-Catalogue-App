from django.urls import path
from . import views

# Authentication URLs
auth_urls = [
    path("login/", views.login_page, name='login'),
    path('redir', views.redir, name="redir"),
    path("logout", views.logout_view, name="logout_view"),
]

# Collection-related URLs
collection_urls = [
    path("collections/", views.CollectionsFrontView.as_view(), name='collections'),
    path("collections/<int:collection_id>/unauthorized/", views.unauthorized_collection_view,
         name="unauthorized_collection"),
]

# Item-related URLS
item_urls = [
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('item/<int:pk>/edit/', views.ItemEditView.as_view(), name='item_edit'),
    path('item/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
]

# Librarian-related URLs
librarian_urls = [
    path('librarian/', views.librarian_page, name='librarian'),
    path('librarian/settings/', views.librarian_settings_view, name='librarian_settings'),
    path('librarian/create_collection_item/', views.create_collection_item, name='create_collection_item'),
    path('librarian/manage_collections/', views.manage_collections, name='manage_collections'),
    path('librarian/manage_collections/edit_collection/<slug:title>/<int:collection_id>/', views.edit_collection,
         name='edit_collection'),
    path('librarian/manage_collections/delete_collection/<slug:title>/<int:collection_id>/', views.delete_collection,
         name='delete_collection'),
    path('librarian/manage_collections/view_requests/<int:collection_id>/', views.view_private_collection_requests,
         name='view_requests'),
    path('librarian/manage_collections/all_private_requests/', views.all_private_requests, name='all_private_requests'),
]

# Patron-related URLS
patron_urls = [
    path('patron/', views.patron_page, name='patron'),
    path('patron/settings/', views.patron_settings_view, name='patron_settings'),
    path('patron/create_collection/', views.create_collection_patron, name='create_collection_patron'),
    path('patron/manage_collections/', views.manage_collections_patron, name='manage_collections_patron'),
    path('patron/manage_collections/edit_collection/<slug:title>/<int:collection_id>/', views.edit_collection_patron,
         name='edit_collection_patron'),
    path('patron/manage_collections/delete_collection/<slug:title>/<int:collection_id>/',
         views.delete_collection_patron, name='delete_collection_patron'),
]

urlpatterns = auth_urls + item_urls + collection_urls + item_urls + librarian_urls + patron_urls

