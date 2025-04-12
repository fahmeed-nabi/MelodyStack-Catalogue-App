from django.contrib.auth import get_user, logout, get_user_model
from django.shortcuts import render, redirect, get_object_or_404
from music.models import Librarian, Patron
from django.contrib import messages
from django.utils import timezone
from mysite.settings import os.environ.get('BUCKET_NAME')

def login_page(request):
    curr_user = get_user(request)
    if curr_user.is_anonymous:
        return render(request, "music/login_page.html")

    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if librarians.exists():
        return redirect("librarian")
    elif patrons.exists():
        return redirect("patron")
    else:
        return render(request, "music/login_page.html")


def redir(request):
    curr_user = get_user(request)
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)
    list(messages.get_messages(request))

    if librarians.exists():
        return redirect("librarian")
    elif patrons.exists():
        return redirect("patron")
    else:
        new_patron = Patron.objects.create(
            user=curr_user,
            name=curr_user.email,
            google_account=curr_user.email,
            date_joined=timezone.now()
        )
        return redirect("patron")

def logout_view(request):
    logout(request)
    return redirect("login")