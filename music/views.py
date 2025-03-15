from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user, logout
from datetime import datetime
from django.views.generic import ListView, DetailView

from . import aws
from .models import Item, Librarian, Patron, Collection
from .forms import SettingsForm, LibrarianSettingsForm, CollectionForm, ItemForm
from . import utils
from .utils import get_user_type, get_accessible_collections

AWS_BUCKET_NAME = 'os.environ.get('BUCKET_NAME')'

def login_page(request):
    curr_user = get_user(request)
    if (curr_user.is_anonymous):
        return render(request, "music/login_page.html")

    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if (librarians.exists()):
        return redirect("librarian")
    elif (patrons.exists()):
        return redirect("patron")
    else:
        return render(request, "music/login_page.html")


def redir(request):
    curr_user = get_user(request)
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if (librarians.exists()):
        return redirect("librarian")
    elif (patrons.exists()):
        return redirect("patron")
    else:
        new_patron = Patron.objects.create(
            user=curr_user,
            name=curr_user.email,
            google_account=curr_user.email,
            date_joined=datetime.now()
        )
        return redirect("patron")


class CollectionsFrontView(ListView):
    template_name = "music/collections_page.html"
    context_object_name = "items"

    def get_queryset(self):
        """
        Returns items based on the selected collection, with privacy checks.
        """
        collection_id = self.request.GET.get("collection")
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)  # "Librarian", "Patron", or "Anonymous"

        if collection_id:
            collection = get_object_or_404(Collection, id=collection_id)

            # Librarians can see all collections, Patrons can see accessible ones
            if collection.public or user_type == 'Librarian' or (
                    user_type == 'Patron' and collection.is_accessible_by(curr_user)):
                items = collection.items.all()
            else:
                return Item.objects.none()  # Return empty queryset for unauthorized access

            # Attach file URLs
            for item in items:
                if item.image:
                    item.file_url = aws.generate_url(item.image.name, AWS_BUCKET_NAME)

            return items  # Return early when filtering by collection

        # Default: show all items that the user has access to
        if user_type == 'Librarian':
            items = Item.objects.all()
        elif user_type == 'Patron':
            no_collection_items = Item.objects.filter(collections__isnull=True)
            accessible_collections = get_accessible_collections(curr_user)
            accessible_items = Item.objects.filter(collections__in=accessible_collections)
            items = accessible_items.union(no_collection_items)
        else:  # Anonymous users
            no_collection_items = Item.objects.filter(collections__isnull=True)
            public_collection_items = Item.objects.filter(collections__public=True)
            items = no_collection_items.union(public_collection_items)

        # Attach file URLs
        for item in items:
            if item.image:
                item.file_url = aws.generate_url(item.image.name, AWS_BUCKET_NAME)

        return items

    def get_context_data(self, **kwargs):
        """
        Add all collections and the selected collection to the context.
        """
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)  # "Librarian", "Patron", or "Anonymous"

        context = super().get_context_data(**kwargs)
        collection_id = self.request.GET.get("collection")

        # Only include collections that are public, or those accessible to the user
        if user_type in ["Librarian", "Patron"]:
            context["collections"] = get_accessible_collections(curr_user)
        else:
            # For Anonymous users, only show public collections
            context["collections"] = Collection.objects.filter(public=True)

        context["active_collection"] = None
        if collection_id:
            context["active_collection"] = get_object_or_404(Collection, id=collection_id)

        context["user_type"] = user_type  # Add user_type to context for use in the template

        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = "music/item_detail.html"
    context_object_name = "item"

    def get_object(self):
        """
        Fetches the item based on its primary key (id).
        """
        return get_object_or_404(Item, id=self.kwargs.get('pk'))

@login_required
def librarian_page(request):
    curr_user = get_user(request)
    librarian = Librarian.objects.filter(user=curr_user).first()

    file_url = aws.generate_url(librarian.profile_picture.name, AWS_BUCKET_NAME)

    return render(request, "music/librarian.html", {
        'librarian_email' : librarian.user.email,
        'librarian_first_name' : librarian.user.first_name,
        'librarian_profile_picture' : librarian.profile_picture,
        'librarian_profile_picture_url' : file_url,
        'librarian_date_joined' : librarian.date_joined.strftime("%B %d, %Y"),
        'librarian_bio' : librarian.bio,
    })


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def patron_page(request):
    curr_user = get_user(request)
    patron = Patron.objects.filter(user=curr_user).first()

    file_url = aws.generate_url(patron.profile_picture.name, AWS_BUCKET_NAME)

    return render(request, "music/patron.html", {
        'patron_email' : patron.user.email,
        'patron_first_name' : patron.user.first_name,
        'patron_profile_picture' : patron.profile_picture,
        'patron_profile_picture_url' : file_url,
        'patron_date_joined' : patron.date_joined.strftime("%B %d, %Y"),
        'patron_bio' : patron.bio,
    })


@login_required
def patron_settings_view(request):
    curr_user = get_user(request)
    patron = Patron.objects.filter(user=curr_user).first()

    file_url = aws.generate_url(patron.profile_picture.name, AWS_BUCKET_NAME)

    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=patron)
        if form.is_valid():
            form.save()
            success_message = "Changes saved successfully!"  # Set the success message
            return render(request, 'music/patron_settings.html',
                          {
                              'form': form,
                              'patron_first_name': patron.user.first_name,
                              'patron_profile_picture': patron.profile_picture,
                              'patron_profile_picture_url': file_url,
                              'patron_bio': patron.bio,
                              'patron_birthday': patron.birthday,
                              'success_message': success_message,
                          })
        else:
            print(form.errors)
    else:
        form = SettingsForm(instance=request.user)

    return render(request, 'music/patron_settings.html', {
        'form' : form,
        'patron_first_name' : patron.user.first_name,
        'patron_profile_picture' : patron.profile_picture,
        'patron_profile_picture_url' : file_url,
        'patron_bio' : patron.bio,
        'patron_birthday' : patron.birthday,
    })


@login_required
def librarian_settings_view(request):
    curr_user = get_user(request)
    librarian = Librarian.objects.filter(user=curr_user).first()

    file_url = aws.generate_url(librarian.profile_picture.name, AWS_BUCKET_NAME)

    if request.method == 'POST':
        form = LibrarianSettingsForm(request.POST, request.FILES, instance=librarian)
        if form.is_valid():
            form.save()
            success_message = "Changes saved successfully!"  # Set the success message
            return render(request, 'music/librarian_settings.html',
                          {
                              'form': form,
                              'librarian_first_name': librarian.user.first_name,
                              'librarian_profile_picture': librarian.profile_picture,
                              'librarian_profile_picture_url': file_url,
                              'librarian_bio': librarian.bio,
                              'librarian_birthday': librarian.birthday,
                              'success_message': success_message,  # Include success message in context
                          })
        else:
            print(form.errors)
    else:
        form = LibrarianSettingsForm(instance=librarian)

    return render(request, 'music/librarian_settings.html', {
        'form': form,
        'librarian_first_name': librarian.user.first_name,
        'librarian_profile_picture': librarian.profile_picture,
        'librarian_profile_picture_url': file_url,
        'librarian_bio': librarian.bio,
        'librarian_birthday': librarian.birthday,
    })


@login_required
def create_collection_item(request):
    if request.method == 'POST':
        collection_form = CollectionForm(request.POST)
        item_form = ItemForm(request.POST, request.FILES)

        if "submit_collection" in request.POST:  # User is submitting a Collection
            if collection_form.is_valid():
                title = collection_form.cleaned_data['title']
                if Collection.objects.filter(title=title).exists():  # Check for duplicate title
                    messages.error(request, f"A Collection with the title '{title}' already exists.")
                else:
                    collection_form.save()
                    return redirect('collections')  # Redirect to collections page

        if "submit_item" in request.POST:  # User is submitting an Item
            if item_form.is_valid():
                description = item_form.cleaned_data['description']
                if not description.strip():  # Ensure description is not empty
                    messages.error(request, "Item description is required.")
                else:
                    item_form.save()
                    messages.success(request, "Item created successfully!")
                    return redirect('collections')  # Redirect to collections page

    else:
        collection_form = CollectionForm()
        item_form = ItemForm()

    # Render the form with error messages and other required context
    return render(request, 'music/create_collection_item.html', {
        'collection_form': collection_form,
        'item_form': item_form,
        'all_patrons': Patron.objects.all(),
        'all_collections': Collection.objects.all(),
        'media_type': Item.MEDIA_TYPE_CHOICES,
        'status': Item.STATUS_CHOICES,
    })