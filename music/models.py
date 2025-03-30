from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from . import aws
from mysite.settings import os.environ.get('BUCKET_NAME')

User = get_user_model()

# Create your models here.
class Item(models.Model):
    STATUS_CHOICES = [
        ('CHECKED_IN', 'Checked In'),
        ('IN_CIRCULATION', 'In Circulation'),
        ('BEING_REPAIRED', 'Being Repaired'),
        ('BORROWED', 'Borrowed'),
    ]
    MEDIA_TYPE_CHOICES = [
        ('CD', 'CD'),
        ('VINYL', 'Vinyl'),
        ('BLU_RAY', 'Blu-ray'),
        ('CASSETTE', 'Cassette Tape')
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='CHECKED_IN'
    )
    location = models.CharField(max_length=255, default="Home Library", blank=True, null=True)
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPE_CHOICES, default='OTHER',
    )
    image = models.ImageField(
        default=None, upload_to='item_images', blank=True, null=True
    )
    collections = models.ManyToManyField('Collection', related_name='items', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    average_rating = models.FloatField(default=0.0)

    owner = models.ForeignKey(User, related_name="owner", on_delete=models.CASCADE, blank=True)

    tags = models.CharField(max_length=255, blank=True, null=True)  # comma-separated list of tags
    due_date = models.DateField(blank=True, null=True)

    def is_accessible_by(self, user):
        """
        Check if a user can access this item.
        An item is accessible if:
        - It belongs to at least one public collection.
        - It belongs to a private collection that the user has access to.
        """
        if self.collections.filter(public=True).exists() or self.collections is None:
            return True
        try:
            patron = Patron.objects.get(user=user)
            return self.collections.filter(private_users=patron).exists()
        except Patron.DoesNotExist:
            return False

    def delete(self, *args, **kwargs):
        if self.image:
            aws.delete_file(self.image.name, os.environ.get('BUCKET_NAME'))
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title


class Patron(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patron_user", default=None)
    name = models.CharField(max_length=200)
    google_account = models.CharField(max_length=200)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    date_joined = models.DateTimeField('date_joined')

    saved_items = models.ManyToManyField(Item, related_name='saved_items', blank=True)
    borrowed_items = models.ManyToManyField(Item, related_name='borrowed_items', blank=True)
    ratings_by = models.ManyToManyField('Rating', related_name='ratings_by', blank=True)
    comments_by = models.ManyToManyField('Comment', related_name='comments_by', blank=True)

    # Optional info
    bio = models.CharField(max_length=250, blank=True)
    birthday = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.profile_picture:
            aws.delete_file(self.profile_picture.name, os.environ.get('BUCKET_NAME'))
        super().delete(*args, **kwargs)

    def get_user_type(self):
        return 'Patron'

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Patron.objects.get(pk=self.pk)
                # If a new profile picture is being uploaded, delete the old one
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    aws.delete_file(old_instance.profile_picture.name, os.environ.get('BUCKET_NAME'))
            except Patron.DoesNotExist:
                pass

        super().save(*args, **kwargs)


class Collection(models.Model):
    title = models.CharField(max_length=100)  # Title of the collection (genre)
    description = models.TextField(max_length=500, blank=True, null=True)  # Optional
    public = models.BooleanField(default=True)  # Whether the collection is public or private
    private_users = models.ManyToManyField(
        Patron, related_name='accessible_collections', blank=True,  
    )  # Patrons allowed to view private collections
    pending_users = models.ManyToManyField(
        Patron, related_name='pending_collections', blank=True,
    ) # Patrons who requested access to a private collection

    # Only assign to Patron since Librarian can access/edit any Collection
    creator = models.ForeignKey('Patron', on_delete=models.CASCADE, related_name='creator', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_accessible_by(self, user):
        """
        Check if a user can access this collection
        """
        if self.public:
            return True
        try:
            patron = Patron.objects.get(user=user)
            return self.private_users.filter(id=patron.id).exists()
        except Patron.DoesNotExist:
            return False

    # Delete all items associated with this collection
    def delete(self, *args, **kwargs):
        self.items.all().delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.title


class Rating(models.Model):
    item = models.ForeignKey(Item, related_name='ratings', on_delete=models.CASCADE)
    patron = models.ForeignKey(Patron, related_name='ratings', on_delete=models.CASCADE)
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Ratings from 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('item', 'patron')  # Ensures that each patron can only rate an item once

    def __str__(self):
        return f"{self.patron.name} rated {self.item.title} - {self.score}"


class Comment(models.Model):
    item = models.ForeignKey(Item, related_name='comments', on_delete=models.CASCADE)
    patron = models.ForeignKey(Patron, related_name='comments', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    thumbs_up = models.IntegerField(default=0)

    def __str__(self):
        return f"Comment by {self.patron.name} on {self.item.title}"


class Librarian(models.Model):
    primary_key = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="librarian_user", default=None)
    name = models.CharField(max_length=200)
    google_account = models.CharField(max_length=200)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    date_joined = models.DateTimeField('date_joined')

    # Optional info
    bio = models.CharField(max_length=250, blank=True)
    birthday = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.profile_picture:
            aws.delete_file(self.profile_picture.name, os.environ.get('BUCKET_NAME'))
        super().delete(*args, **kwargs)

    def get_user_type(self):
        return 'Librarian'

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Librarian.objects.get(pk=self.pk)
                # If a new profile picture is being uploaded, delete the old one
                if old_instance.profile_picture and old_instance.profile_picture != self.profile_picture:
                    aws.delete_file(old_instance.profile_picture.name, os.environ.get('BUCKET_NAME'))
            except Librarian.DoesNotExist:
                pass

        super().save(*args, **kwargs)

class BorrowRequest(models.Model):
    requested_item = models.ForeignKey(Item, related_name="requested_item", on_delete=models.CASCADE)
    item_owner = models.ForeignKey(User, related_name="item_owner", on_delete=models.CASCADE)
    requesters = models.ManyToManyField('BorrowRequester', related_name="requesters", blank=True)

class BorrowRequester(models.Model):
    STATUS_CHOICES = [
        ('APPROVED', 'Approved'),
        ('PENDING', 'Pending'),
        ('DENIED', 'Denied')
    ]

    request_user = models.OneToOneField(User, related_name="request_user", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDING'
    )
    associated_request = models.ForeignKey(BorrowRequest, related_name="associated_request", on_delete=models.CASCADE)
