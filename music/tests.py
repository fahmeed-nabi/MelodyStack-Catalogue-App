from django.test import TestCase
from django.urls import reverse

# Create your tests here.

class RenderLoginPage(TestCase):
    def test_render_login_page(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

class RenderingAnonymousFrontPage(TestCase):
    def test_render_anonymous_front_page(self):
        response = self.client.get(reverse("public"))
        self.assertEqual(response.status_code, 200)