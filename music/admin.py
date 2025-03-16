from django.contrib import admin
from .models import Item, Patron, Librarian, Collection

# Register your models here.
class PatronAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined", "profile_picture"]

class LibrarianAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined", "profile_picture"]

class CollectionAdmin(admin.ModelAdmin):
    fields = ["title", "description", "public", "private_users", "image"]

admin.site.register(Item)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Librarian, LibrarianAdmin)
admin.site.register(Patron, PatronAdmin)
