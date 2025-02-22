from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user, logout
from datetime import datetime

from django.views.generic import ListView

from .models import Item, Librarian, Patron


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
        """
        # Query for items not in any collection
        no_collection_items = Item.objects.filter(collections__isnull=True)

        # Query for items in public collections
        public_collection_items = Item.objects.filter(collections__public=True)

        # Combine the two querysets using union (duplicates are excluded by default)
        return no_collection_items.union(public_collection_items)


def librarian_page(request):
    curr_user = get_user(request)
    librarian = Librarian.objects.filter(user=curr_user).first()
    return render(request, "music/librarian.html", {
        'librarian': librarian.user.email
    })


def logout_view(request):
    logout(request)
    return redirect("login")


def patron_page(request):
    curr_user = get_user(request)
    patron = Patron.objects.filter(user=curr_user).first()
    return render(request, "music/patron.html", {
        'patron': patron.user.email
    })
