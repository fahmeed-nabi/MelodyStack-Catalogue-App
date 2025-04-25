from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from music.models import Patron, Librarian
from music.views import redir

User = get_user_model()