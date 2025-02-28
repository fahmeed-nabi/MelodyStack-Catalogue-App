from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user, logout
from datetime import datetime

from django.views.generic import ListView, DetailView

from .models import Item, Librarian, Patron, Collection


def login_page(request):
    curr_user = get_user(request)
    if (curr_user.is_anonymous):
        return render(request, "music/login_page.html")

    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if (librarians.exists()):
        return redirect("librarian")
    elif (patrons.exists()):
        return redirect("patron")
    else:
        return render(request, "music/login_page.html")


def redir(request):
    curr_user = get_user(request)
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if (librarians.exists()):
        return redirect("librarian")
    elif (patrons.exists()):
        return redirect("patron")
    else:
        new_patron = Patron.objects.create(
            user=curr_user,
            name=curr_user.email,
            google_account=curr_user.email,
            date_joined=datetime.now()
        )
        return redirect("patron")


class AnonymousFrontView(ListView):
    template_name = "music/anonymous_front.html"
    context_object_name = "items"

    def get_queryset(self):
        """
        Returns a queryset of items that anonymous users are allowed to see:
        - Items not in any collection
        - Items in public collections
        - Optionally filtered by a specific collection
        """
        collection_id = self.request.GET.get('collection')

        if collection_id:
            # Filter items that are either in the selected public collection or not in any collection
            no_collection_items = Item.objects.filter(collections__isnull=True)
            public_collection_items = Item.objects.filter(collections__id=collection_id, collections__public=True)
        else:
            # Show all public items when no collection is selected
            no_collection_items = Item.objects.filter(collections__isnull=True)
            public_collection_items = Item.objects.filter(collections__public=True)

        # Merge both queries using `union()`
        return no_collection_items.union(public_collection_items)

    def get_context_data(self, **kwargs):
        """
        Adds available collections to the context for sidebar filtering.
        """
        context = super().get_context_data(**kwargs)
        context['collections'] = Collection.objects.filter(public=True)
        return context
    
class ItemDetailView(DetailView):
    model = Item
    template_name = "music/item_detail.html"
    context_object_name = "item"

    def get_object(self):
        """
        Fetches the item based on its primary key (id).
        """
        return get_object_or_404(Item, id=self.kwargs.get('pk'))

def librarian_page(request):
    curr_user = get_user(request)
    librarian = Librarian.objects.filter(user=curr_user).first()
    return render(request, "music/librarian.html", {
        'librarian_email' : librarian.user.email,
        'librarian_first_name' : librarian.user.first_name
    })


def logout_view(request):
    logout(request)
    return redirect("login")


def patron_page(request):
    curr_user = get_user(request)
    patron = Patron.objects.filter(user=curr_user).first()
    return render(request, "music/patron.html", {
        'patron_email' : patron.user.email,
        'patron_first_name' : patron.user.first_name
    })
