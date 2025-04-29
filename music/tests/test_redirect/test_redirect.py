from django.contrib.auth import get_user_model
from django.test import override_settings, TestCase
from django.urls import reverse
from django.utils import timezone

from music.models import BorrowRequest, Collection, Item, Patron, Librarian

User = get_user_model()

# These test cases test authentication redirects
@override_settings(SECURE_SSL_REDIRECT=False)
class TestAuthRedirects(TestCase):

    # Sets up test user
    def setUp(self):

        self.test_user = User.objects.create(
            username="test_user",
            first_name="Test",
            last_name="User",
            email="test_user@example.com"
        )
        self.test_user.save()
        self.client.force_login(self.test_user)

    # Tests automatic creation of patron on new user login
    def test_patron_redirect_new_user(self):

        response = self.client.get(reverse("redir"))

        self.assertEqual(Patron.objects.count(), 1)
        self.assertEqual(Patron.objects.filter(name="test_user@example.com").count(), 1)
        self.assertFalse(Librarian.objects.exists())

        self.assertRedirects(response, reverse("patron"))

    # Tests existing patron login
    def test_patron_redirect_existing_user(self):

        test_patron = Patron.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now()
        )
        test_patron.save()

        response = self.client.get(reverse("redir"))
        
        self.assertEqual(Patron.objects.count(), 1)
        self.assertEqual(Patron.objects.filter(name="Test User").count(), 1)
        self.assertFalse(Librarian.objects.exists())

        self.assertRedirects(response, reverse("patron"))
    
    # Tests existing librarian login
    def test_librarian_redirect_existing_user(self):

        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now()
        )
        test_librarian.save()

        response = self.client.get(reverse("redir"))
        
        self.assertFalse(Patron.objects.exists())       
        self.assertEqual(Librarian.objects.count(), 1)
        self.assertEqual(Librarian.objects.filter(name="Test User").count(), 1)

        self.assertRedirects(response, reverse("librarian"))
    
    # Tests logout
    def test_user_redirect_logout(self):
        
        response = self.client.get(reverse("logout_view"))
        
        self.assertRedirects(response, reverse("login"))

# These test cases test borrowing system redirects
@override_settings(SECURE_SSL_REDIRECT=False)
class TestBorrowRedirects(TestCase):

    # Sets up test user
    def setUp(self):

        self.test_user = User.objects.create(
            username="test_user",
            first_name="Test",
            last_name="User",
            email="test_user@example.com"
        )
        self.test_user.save()
        self.client.force_login(self.test_user)
    
    # Tests borrow redirect
    def test_borrow_redirect(self):

        test_item = Item.objects.create(title="Test Item",)
        test_item.save()

        response = self.client.get(reverse("borrow_redirect", kwargs={"pk": test_item.pk}))

        self.assertEqual(BorrowRequest.objects.count(), 1)
        self.assertEqual(BorrowRequest.objects.filter(requested_item=test_item, requester=self.test_user,).count(), 1)

        self.assertRedirects(response, reverse("item_detail", kwargs={"pk": test_item.pk}))
    
    # Tests return redirect
    def test_return_redirect(self):

        test_item = Item.objects.create(title="Test Item",)
        test_item.save()
        test_borrow_request_object = BorrowRequest.objects.create(requested_item=test_item, requester=self.test_user,)
        test_borrow_request_object.save()

        response = self.client.get(reverse("return_redirect", kwargs={"pk": test_borrow_request_object.pk}))

        self.assertEqual(test_item.status, "CHECKED_IN")
        self.assertFalse(BorrowRequest.objects.exists())

        self.assertRedirects(response, reverse("outgoing_requests"))
    
    # Tests approve borrow request redirect
    def test_approve_borrow_request_redirect(self):
        
        test_second_user = User.objects.create(
            username="test_second_user",
            first_name="Test",
            last_name="User",
            email="test_second_user@example.com"
        )
        test_second_user.save()
        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()
        test_item = Item.objects.create(title="Test Item",)
        test_item.save()
        test_borrow_request_object = BorrowRequest.objects.create(requested_item=test_item, requester=self.test_user,)
        test_borrow_request_object.save()
        test_second_borrow_request_object = BorrowRequest.objects.create(requested_item=test_item, requester=test_second_user,)
        test_second_borrow_request_object.save()

        response = self.client.get(reverse("approve_request", kwargs={"borrow_request_id": test_borrow_request_object.pk, "user_id": self.test_user.pk,}))

        self.assertEqual(BorrowRequest.objects.count(), 2)
        self.assertEqual(BorrowRequest.objects.filter(requested_item=test_item, requester=self.test_user, status="APPROVED").count(), 1)
        self.assertEqual(BorrowRequest.objects.filter(requested_item=test_item, requester=test_second_user, status="DENIED").count(), 1)
        self.assertEqual(Item.objects.get(pk=test_item.pk).status, "IN_CIRCULATION")

        self.assertRedirects(response, reverse("incoming_requests"))
    
    # Tests deny borrow request redirect
    def test_deny_borrow_request_redirect(self):

        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()
        test_item = Item.objects.create(title="Test Item",)
        test_item.save()
        test_borrow_request_object = BorrowRequest.objects.create(requested_item=test_item, requester=self.test_user,)
        test_borrow_request_object.save()

        response = self.client.get(reverse("deny_request", kwargs={"borrow_request_id": test_borrow_request_object.pk, "user_id": self.test_user.pk,}))

        self.assertEqual(BorrowRequest.objects.count(), 1)
        self.assertEqual(BorrowRequest.objects.filter(requested_item=test_item, requester=self.test_user, status="DENIED").count(), 1)

        self.assertRedirects(response, reverse("incoming_requests"))

# These test cases test item/collection creation redirects
@override_settings(SECURE_SSL_REDIRECT=False)
class TestItemCollectionCreationRedirects(TestCase):

    # Sets up test user
    def setUp(self):

        self.test_user = User.objects.create(
            username="test_user",
            first_name="Test",
            last_name="User",
            email="test_user@example.com"
        )
        self.test_user.save()
        self.client.force_login(self.test_user)
    
    # Tests create item redirect, no audio
    def test_create_item_no_audio_redirect(self):

        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()
        test_collection = Collection.objects.create(title="Test Collection",)
        test_collection.save()
        test_second_collection = Collection.objects.create(title="Test Collection 2",)
        test_second_collection.save()

        title = "Test Title"
        description = "Test Description"
        status = "CHECKED_IN"
        location = "Test Location"
        media_type = "CD"
        collections = [str(test_collection.pk), str(test_second_collection.pk)]
        tags = "Test Tag 1, Test Tag 2"
        genre = "Test Genre"

        response = self.client.post(reverse("create_collection_item"), data={
            "title": title,
            "description": description,
            "status": status,
            "location": location,
            "media_type": media_type,
            "collections": collections,
            "tags": tags,
            "genre": genre,
            "submit_item": "",
        })

        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.title, title)
        self.assertEqual(item.description, description)
        self.assertEqual(item.status, status)
        self.assertEqual(item.location, location)
        self.assertEqual(item.media_type, media_type)
        self.assertEqual(item.tags, tags)
        self.assertEqual(item.genre, genre)
        
        self.assertEqual(Collection.objects.count(), 2)
        self.assertEqual(Collection.objects.filter(items__id=item.pk, id=test_collection.pk).count(), 1)
        self.assertEqual(Collection.objects.filter(items__id=item.pk, id=test_second_collection.pk).count(), 1)

        self.assertRedirects(response, reverse("collections"))

    # Tests create item redirect, valid audio
    def test_create_item_valid_audio_redirect(self):
        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()

        title = "Test Title"
        description = "Test Description"
        status = "CHECKED_IN"
        location = "Test Location"
        media_type = "CD"
        audio_path = "music/tests/test_redirect"
        audio_name = "test_audio.mp3"
        tags = "Test Tag 1, Test Tag 2"
        genre = "Test Genre"

        with open(f"{audio_path}/{audio_name}", "rb") as audio:
            response = self.client.post(reverse("create_collection_item"), data={
                "title": title,
                "description": description,
                "status": status,
                "location": location,
                "media_type": media_type,
                "audio": audio,
                "tags": tags,
                "genre": genre,
                "submit_item": "",
            })

        self.assertEqual(Item.objects.count(), 1)
        item = Item.objects.first()
        self.assertEqual(item.title, title)
        self.assertEqual(item.description, description)
        self.assertEqual(item.status, status)
        self.assertEqual(item.location, location)
        self.assertEqual(item.media_type, media_type)
        self.assertEqual(item.audio.name, f"{Item.audio.field.upload_to}/{audio_name}")
        self.assertEqual(item.tags, tags)
        self.assertEqual(item.genre, genre)

        self.assertRedirects(response, reverse("collections"))

    # Tests create item redirect, invalid audio
    def test_create_item_invalid_audio_redirect(self):
        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()

        title = "Test Title"
        description = "Test Description"
        status = "CHECKED_IN"
        location = "Test Location"
        media_type = "CD"
        audio_name = "music/tests/test_redirect/invalid_audio.png"
        tags = "Test Tag 1, Test Tag 2"
        genre = "Test Genre"

        with open(audio_name, "rb") as audio:
            response = self.client.post(reverse("create_collection_item"), data={
                "title": title,
                "description": description,
                "status": status,
                "location": location,
                "media_type": media_type,
                "audio": audio,
                "tags": tags,
                "genre": genre,
                "submit_item": "",
            })
        
        self.assertEqual(Item.objects.count(), 0)
    
    # Tests create collection redirect
    def test_create_collection_redirect(self):

        test_librarian = Librarian.objects.create(
            user=self.test_user,
            name="Test User",
            google_account="test_user@example.com",
            date_joined=timezone.now(),
        )
        test_librarian.save()
        test_patron_user = User.objects.create(
            username="test_patron_user",
            first_name="Test",
            last_name="Patron",
            email="test_patron_user@example.com",
        )
        test_patron_user.save()
        test_patron = Patron.objects.create(
            user=test_patron_user,
            name="Test Patron",
            google_account="test_patron_user@example.com",
            date_joined=timezone.now(),
        )
        test_patron.save()
        test_second_patron_user = User.objects.create(
            username="test_second_patron_user",
            first_name="Second",
            last_name="Patron",
            email="test_second_patron_user@example.com",
        )
        test_second_patron_user.save()
        test_second_patron = Patron.objects.create(
            user=test_second_patron_user,
            name="Second Patron",
            google_account="test_second_patron_user@example.com",
            date_joined=timezone.now(),
        )
        test_second_patron.save()

        title = "Test Title"
        description = "Test Description"
        private_users = [str(test_patron.pk), str(test_second_patron.pk)]

        response = self.client.post(reverse("create_collection_item"), data={
            "title": title,
            "description": description,
            "private_users": private_users,
            "submit_collection": "",
        })

        self.assertEqual(Collection.objects.count(), 1)
        collection = Collection.objects.first()
        self.assertEqual(collection.title, title)
        self.assertEqual(collection.description, description)

        self.assertEqual(Patron.objects.count(), 2)
        self.assertEqual(Patron.objects.filter(accessible_collections__id=collection.pk, id=test_patron.pk).count(), 1)
        self.assertEqual(Patron.objects.filter(accessible_collections__id=collection.pk, id=test_second_patron.pk).count(), 1)

        self.assertRedirects(response, reverse("collections"))