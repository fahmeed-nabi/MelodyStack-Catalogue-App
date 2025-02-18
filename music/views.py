from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic

from .models import Item, Librarian, Patron

def login_page(request):
    return render(request, "music/login_page.html")

def anonymous_front(request):
    return render(request, "music/anonymous_front.html")

# class anonymous_front(generic.ListView):
#     template_name = "music/anonymous_front.html"
#     context_object_name = "items" # TODO: implement Item model
#
#     def get_queryset(self):
#         return Item.objects.all() # TODO: implement Item model

def librarian_page(request, user_id):
    librarian = get_object_or_404(Librarian, pk=user_id)
    return render(request, "music/librarian.html", {
        'librarian' : librarian
    })

def patron_page(request, user_id):
    patron = get_object_or_404(Patron, pk=user_id)
    return render(request, "music/patron.html", {
        'patron' : patron
    })
