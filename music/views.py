from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

# Create your views here.

def login_page(request):
    return render(request, "music/login_page.html")
