from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user, logout
from datetime import datetime

from .models import Item, Librarian, Patron

def login_page(request):
    curr_user = get_user(request)
    if(curr_user.is_anonymous):
        return render(request, "music/login_page.html")
    
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)
    
    if(librarians.exists()):
        return redirect("librarian")
    elif(patrons.exists()):
        return redirect("patron")
    else:
        return render(request, "music/login_page.html")

def redir(request):
    curr_user = get_user(request)
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)
    
    if(librarians.exists()):
        return redirect("librarian")
    elif(patrons.exists()):
        return redirect("patron")
    else:
        new_patron = Patron.objects.create(
            user = curr_user,
            name = curr_user.email,
            google_account = curr_user.email,
            date_joined = datetime.now()
        )
        return redirect("patron")
       

def anonymous_front(request):
    return render(request, "music/anonymous_front.html")

# class anonymous_front(generic.ListView):
#     template_name = "music/anonymous_front.html"
#     context_object_name = "items" # TODO: implement Item model
#
#     def get_queryset(self):
#         return Item.objects.all() # TODO: implement Item model

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
