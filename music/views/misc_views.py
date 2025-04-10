from django.contrib.auth import get_user
from django.shortcuts import render

from music.utils import get_user_type


def help_page(request):
    user_type = get_user_type(get_user(request))
    return render(request, "music/help.html", {
        "user_type": user_type,
    })

def about_page(request):
    user_type = get_user_type(request.user)
    return render(request, "music/about.html", {
        "user_type": user_type,
    })
