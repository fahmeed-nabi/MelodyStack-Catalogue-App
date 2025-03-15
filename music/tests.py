from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your tests here.

class RenderLoginPage(TestCase):
    def test_render_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
class RenderingAnonymousFrontPage(TestCase):
    def test_render_anonymous_front_page(self):
        response = self.client.get(reverse("public"))
        self.assertEqual(response.status_code, 200)

class TestPatronRendering(TestCase):
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

    def test_patron_rendering(self):
        print("Testing user name: ", self.user.username)
        self.assertEqual(self.user.username, "testinguser")


    