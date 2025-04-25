from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from music.models import Librarian, Patron

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

# These test cases test rendering of patron pages
# Uses patron user
@override_settings(SECURE_SSL_REDIRECT=False)
class RenderPatronPages(TestCase):

    # Sets up test patron
    def setUp(self):
        username="test_patron"
        email="test_patron@example.com"
        first_name="Test"
        last_name="Patron"

        self.test_user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        self.client.force_login(self.test_user)

        user = self.test_user
        name = first_name + " " + last_name
        google_account = email
        date_joined = timezone.now()

        self.test_patron = Patron.objects.create(
            user=user,
            name=name,
            google_account=google_account,
            date_joined=date_joined,
        )

    # Makes sure patron page is rendered with no errors
    def test_render_patron_page(self):
        response = self.client.get(reverse("patron"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron settings page is rendered with no errors
    def test_render_patron_settings_page(self):
        response = self.client.get(reverse("patron_settings"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron create collection page is rendered with no errors
    def test_render_patron_create_collection_page(self):
        response = self.client.get(reverse("create_collection_patron"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron manage collections page is rendered with no errors
    def test_render_patron_manage_collections_page(self):
        response = self.client.get(reverse("manage_collections_patron"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron outgoing requests page is rendered with no errors
    def test_render_patron_outgoing_requests_page(self):
        response = self.client.get(reverse("outgoing_requests"))
        self.assertEqual(response.status_code, 200)

# These test cases test rendering of librarian pages
# Uses librarian user
@override_settings(SECURE_SSL_REDIRECT=False)
class RenderLibrarianPages(TestCase):

    # Sets up test librarian
    def setUp(self):
        username="test_librarian"
        email="test_librarian@example.com"
        first_name="Test"
        last_name="Librarian"

        self.test_user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        self.client.force_login(self.test_user)

        user = self.test_user
        name = first_name + " " + last_name
        google_account = email
        date_joined = timezone.now()

        self.test_librarian = Librarian.objects.create(
            user=user,
            name=name,
            google_account=google_account,
            date_joined=date_joined,
        )
    
    # Makes sure librarian page is rendered with no errors
    def test_render_librarian_page(self):
        response = self.client.get(reverse("librarian"))
        self.assertEqual(response.status_code, 200)

    # Makes sure librarian settings page is rendered with no errors
    def test_render_librarian_settings_page(self):
        response = self.client.get(reverse("librarian_settings"))
        self.assertEqual(response.status_code, 200)

    # Makes sure librarian incoming requests page is rendered with no errors
    def test_render_librarian_incoming_requests_page(self):
        response = self.client.get(reverse("incoming_requests"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian create collection/item page is rendered with no errors
    def test_render_librarian_create_collection_item_page(self):
        response = self.client.get(reverse("create_collection_item"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure manage collections librarian page is rendered with no errors
    def test_render_librarian_manage_collections_page(self):
        response = self.client.get(reverse("manage_collections"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian all private requests page is rendered with no errors
    def test_render_librarian_all_private_requests_page(self):
        response = self.client.get(reverse("all_private_requests"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian outgoing requests page is rendered with no errors
    def test_render_librarian_outgoing_requests_page(self):
        response = self.client.get(reverse("outgoing_requests"))
        self.assertEqual(response.status_code, 200)
    
    # Make sure libaraian promote patron page is rendered with no errors
    def test_render_librarian_promote_patron_page(self):
        response = self.client.get(reverse("promote_patron"))
        self.assertEqual(response.status_code, 200)