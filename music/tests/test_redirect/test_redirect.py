from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from music.models import Patron, Librarian

User = get_user_model()

# These test cases test different redirects
@override_settings(SECURE_SSL_REDIRECT=False)
class TestLoginRedirects(TestCase):

    # Sets up a sample user
    def setUp(self):
        username = "testinguser"
        first_name = "Testing"
        last_name = "User"
        email_address = "test@example.com"
        
        self.user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email_address
            )

    # Tests automatic creation of patron on new user login
    def test_patron_redirect_new_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("redir"))

        self.assertTrue(Patron.objects.filter(name="test@example.com").exists())
        self.assertFalse(Librarian.objects.filter(name="test@example.com").exists())

        self.assertRedirects(response, reverse("patron"))

    # Tests existing patron login
    def test_patron_redirect_existing_user(self):

        existing_patron = Patron.objects.create(
            user=self.user,
            name="Already Exists",
            google_account=self.user.email,
            date_joined=timezone.now()
        )
        existing_patron.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse("redir"))

        
        self.assertTrue(Patron.objects.filter(name="Already Exists").exists())
        self.assertEqual(Patron.objects.filter(name="Already Exists").count(), 1)
        self.assertFalse(Patron.objects.filter(name="test@example.com").exists())
        self.assertFalse(Librarian.objects.filter(name="test@example.com").exists())       

        self.assertRedirects(response, reverse("patron"))
    
    # Tests for existing librarian login
    def test_librarian_redirect_existing_user(self):

        existing_librarian = Librarian.objects.create(
            user=self.user,
            name="Already Exists",
            google_account=self.user.email,
            date_joined=timezone.now()
        )
        existing_librarian.save()

        self.client.force_login(self.user)
        response = self.client.get(reverse("redir"))

        
        self.assertFalse(Patron.objects.filter(name="Already Exists").exists())
        self.assertFalse(Patron.objects.filter(name="test@example.com").exists())
        self.assertTrue(Librarian.objects.filter(name="Already Exists").exists())       
        self.assertEqual(Librarian.objects.filter(name="Already Exists").count(), 1)

        self.assertRedirects(response, reverse("librarian"))