from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from music.models import Patron, Librarian
from music.views import redir

User = get_user_model()

# These test cases test rendering of anonymous pages
# Does not use logged in user
@override_settings(SECURE_SSL_REDIRECT=False)
class RenderAnonymousPages(TestCase):
    
    # Makes sure login page is rendered with no errors
    def test_render_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure public collections page is rendered with no errors
    def test_render_collections_page(self):
        response = self.client.get(reverse("collections"))
        self.assertEqual(response.status_code, 200)