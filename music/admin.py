from django.contrib import admin
from .models import Item, Patron, Librarian, Collection, BorrowRequest, BorrowRequester, Comment

# Register your models here.
class PatronAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined", "profile_picture"]

class LibrarianAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined", "profile_picture"]

class CollectionAdmin(admin.ModelAdmin):
    fields = ["title", "description", "public", "private_users"]

class BorrowRequestAdmin(admin.ModelAdmin):
    fields = ["requested_item", "item_owner", "requesters"]

class BorrowRequesterAdmin(admin.ModelAdmin):
    fields = ["request_user", "status", "associated_request"]

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('item', 'patron', 'created_at', 'thumbs_up')
    search_fields = ('text',)
    

admin.site.register(Item)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Librarian, LibrarianAdmin)
admin.site.register(Patron, PatronAdmin)
admin.site.register(BorrowRequest, BorrowRequestAdmin)
admin.site.register(BorrowRequester, BorrowRequesterAdmin)

