from django.urls import path
from . import views
import music.views.auth_views as auth_views
import music.views.collection_views as cv
import music.views.item_views as item_views
import music.views.patron_views as pv
import music.views.librarian_views as lv
import music.views.misc_views as misc_views

# Authentication URLs
auth_urls = [
    path("login/", auth_views.login_page, name='login'),
    path('redir', auth_views.redir, name="redir"),
    path("logout", auth_views.logout_view, name="logout_view"),
]

# Collection-related URLs
collection_urls = [
    path("collections/", cv.CollectionsFrontView.as_view(), name='collections'),
    path("collections/<int:collection_id>/unauthorized/", cv.unauthorized_collection_view,
         name="unauthorized_collection"),
]

# Item-related URLS
item_urls = [
    path('item/<int:pk>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('item/<int:pk>/edit/', views.ItemEditView.as_view(), name='item_edit'),
    path('item/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('borrow_redir/<int:pk>/', views.borrow_redir, name='borrow_redirect'),
    path('saved-items/', views.saved_items_view, name='saved_items'),
    path('return_redir/<int:pk>', views.return_redir, name='return_redirect')
]

# Librarian-related URLs
librarian_urls = [
    path('librarian/', lv.librarian_page, name='librarian'),
    path('librarian/settings/', lv.librarian_settings_view, name='librarian_settings'),
    path('librarian/incoming_requests', lv.incoming_requests, name='incoming_requests'),
    path('librarian/create_collection_item/', lv.create_collection_item, name='create_collection_item'),
    path('librarian/manage_collections/', lv.manage_collections, name='manage_collections'),
    path('librarian/manage_collections/edit_collection/<slug:title>/<int:collection_id>/', lv.edit_collection,
         name='edit_collection'),
    path('librarian/manage_collections/delete_collection/<slug:title>/<int:collection_id>/', lv.delete_collection,
         name='delete_collection'),
    path('librarian/manage_collections/view_requests/<int:collection_id>/', lv.view_private_collection_requests,
         name='view_requests'),
    path('librarian/manage_collections/all_private_requests/', lv.all_private_requests, name='all_private_requests'),
    path('librarian/incoming_requests/approve_request/<int:borrow_request_id>/<int:user_id>', lv.approve_request,
         name="approve_request"),
    path('librarian/incoming_requests/deny_request/<int:borrow_request_id>/<int:user_id>', lv.deny_request, name="deny_request"),
    path('librarian/outgoing_requests', lv.outgoing_requests, name="outgoing_requests"),
    path('librarian/promote_patron', lv.patron_promotion_view, name="promote_patron"),
    path('librarian/promote_patron_confirmation/<int:patron_id>', lv.patron_promotion_confirmation, name="promote_patron_confirmation"),
]

# Patron-related URLs
patron_urls = [
    path('patron/', pv.patron_page, name='patron'),
    path('patron/settings/', pv.patron_settings_view, name='patron_settings'),
    path('patron/create_collection/', pv.create_collection_patron, name='create_collection_patron'),
    path('patron/manage_collections/', pv.manage_collections_patron, name='manage_collections_patron'),
    path('patron/manage_collections/edit_collection/<slug:title>/<int:collection_id>/', pv.edit_collection_patron,
         name='edit_collection_patron'),
    path('patron/manage_collections/delete_collection/<slug:title>/<int:collection_id>/',
         pv.delete_collection_patron, name='delete_collection_patron'),
    path('patron/outgoing_requests', lv.outgoing_requests, name='outgoing_requests'),
]

# Other URLs
misc_urls = [
    path('help', misc_views.help_page, name='help'),
    path('about', misc_views.about_page, name='about'),
             ]

urlpatterns = auth_urls + item_urls + collection_urls + item_urls + librarian_urls + patron_urls + misc_urls

