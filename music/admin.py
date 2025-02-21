from django.contrib import admin
from .models import Item, Patron, Librarian

# Register your models here.
class PatronAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined"]

class LibrarianAdmin(admin.ModelAdmin):
    fields = ["user", "name", "google_account", "date_joined"]

admin.site.register(Item)
admin.site.register(Librarian, LibrarianAdmin)
admin.site.register(Patron, PatronAdmin)