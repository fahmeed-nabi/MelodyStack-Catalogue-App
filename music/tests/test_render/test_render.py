from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from music.models import Collection, Item, Librarian, Patron

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
    
    # Makes sure help page is rendered with no errors
    def test_render_help_page(self):
        response = self.client.get(reverse("help"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure about page is rendered with no errors
    def test_render_about_page(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

# These test cases test rendering of patron pages
# Uses patron user
@override_settings(SECURE_SSL_REDIRECT=False)
class RenderPatronPages(TestCase):

    # Sets up test user, patron, item, and collection
    def setUp(self):

        # Sets up test user
        self.test_user = User.objects.create(
            username="test_patron",
            first_name="Test",
            last_name="Patron",
            email="test_patron@example.com",
        )
        self.test_user.save()
        self.client.force_login(self.test_user)

        # Sets up test patron
        self.test_patron = Patron.objects.create(
            user=self.test_user,
            name="Test Patron",
            google_account="test_patron@example.com",
            date_joined=timezone.now(),
        )
        self.test_patron.save()

        # Sets up test item
        self.test_item = Item.objects.create(title="Test Item",)
        self.test_item.save()

        # Sets up test collection with test patron as creator
        self.test_collection = Collection.objects.create(title="Test Collection", creator=self.test_patron)
        self.test_collection.save()

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
    
    # Makes sure patron unauthorized collection page is rendered with no errors
    def test_render_patron_unauthorized_collection_page(self):
        response = self.client.get(reverse("unauthorized_collection", kwargs={"collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron item detail page is rendered with no errors
    def test_render_patron_item_detail_page(self):
        response = self.client.get(reverse("item_detail", kwargs={"pk": self.test_item.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron saved items page is rendered with no errors
    def test_render_patron_saved_items_page(self):
        response = self.client.get(reverse("saved_items"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron edit collection page is rendered with no errors
    def test_render_patron_edit_collection_page(self):
        response = self.client.get(reverse("edit_collection_patron", kwargs={"title": slugify(self.test_collection.title), "collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure patron delete collection page is rendered with no errors
    def test_render_patron_delete_collection_page(self):
        response = self.client.get(reverse("delete_collection_patron", kwargs={"title": slugify(self.test_collection.title), "collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)

# These test cases test rendering of librarian pages
# Uses librarian user
@override_settings(SECURE_SSL_REDIRECT=False)
class RenderLibrarianPages(TestCase):

    # Sets up test user, patron, librarian, item, and collection
    def setUp(self):

        # Sets up test patron user
        self.test_patron_user = User.objects.create(
            username="test_patron",
            first_name="Test",
            last_name="Patron",
            email="test_patron@example.com",
        )
        self.test_patron_user.save()
        
        # Sets up test librarian user
        self.test_librarian_user = User.objects.create(
            username="test_librarian",
            first_name="Test",
            last_name="Librarian",
            email="test_librarian@example.com",
        )
        self.test_librarian_user.save()
        self.client.force_login(self.test_librarian_user)

        # Sets up test patron
        self.test_patron = Patron.objects.create(
            user=self.test_patron_user,
            name="Test Patron",
            google_account="test_patron@example.com",
            date_joined=timezone.now()
        )
        self.test_patron.save()

        # Sets up test librarian
        self.test_librarian = Librarian.objects.create(
            user=self.test_librarian_user,
            name="Test Librarian",
            google_account="test_libaraian@example.com",
            date_joined=timezone.now(),
        )
        self.test_librarian.save()

        # Sets up test item
        self.test_item = Item.objects.create(title="Test Item",)
        self.test_item.save()

        # Sets up test private collection
        self.test_collection = Collection.objects.create(title="Test Collection", public=False,)
        self.test_collection.save()
    
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
    
    # Makes sure librarian manage collections page is rendered with no errors
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
    
    # Makes sure libaraian promote patron page is rendered with no errors
    def test_render_librarian_promote_patron_page(self):
        response = self.client.get(reverse("promote_patron"))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian item edit page is rendered with no errors
    def test_render_librarian_item_edit_page(self):
        response = self.client.get(reverse("item_edit", kwargs={"pk": self.test_item.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Make sures librarian item delete page is rendered with no errors
    def test_render_librarian_item_delete_page(self):
        response = self.client.get(reverse("item_delete", kwargs={"pk": self.test_item.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian edit collection page is rendered with no errors
    def test_render_librarian_edit_collection_page(self):
        response = self.client.get(reverse("edit_collection", kwargs={"title": slugify(self.test_collection.title), "collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian delete collection page is rendered with no errors
    def test_render_librarian_delete_collection_page(self):
        response = self.client.get(reverse("delete_collection", kwargs={"title": slugify(self.test_collection.title), "collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian view private collection requests page is rendered with no errors
    def test_render_librarian_view_private_collection_requests_page(self):
        response = self.client.get(reverse("view_requests", kwargs={"collection_id": self.test_collection.pk,}))
        self.assertEqual(response.status_code, 200)
    
    # Makes sure librarian promote patron confirmation page is rendered with no errors
    def test_render_librarian_promote_patron_confirmation_page(self):
        response = self.client.get(reverse("promote_patron_confirmation", kwargs={"patron_id": self.test_patron.pk}))
        self.assertEqual(response.status_code, 200)