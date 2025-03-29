from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.messages.storage import default_storage
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views import generic
from django.contrib.auth import get_user, logout, get_user_model
from django.utils import timezone
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

User = get_user_model()

from . import aws
from .models import Item, Librarian, Patron, Collection, BorrowRequest
from .forms import SettingsForm, LibrarianSettingsForm, CollectionForm, ItemForm, FilterForm
from .utils import get_user_type, get_accessible_collections
from mysite.settings import os.environ.get('BUCKET_NAME')

def login_page(request):
    curr_user = get_user(request)
    if curr_user.is_anonymous:
        return render(request, "music/login_page.html")

    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)

    if librarians.exists():
        return redirect("librarian")
    elif patrons.exists():
        return redirect("patron")
    else:
        return render(request, "music/login_page.html")



def redir(request):
    curr_user = get_user(request)
    librarians = Librarian.objects.filter(user=curr_user)
    patrons = Patron.objects.filter(user=curr_user)
    list(messages.get_messages(request))

    if librarians.exists():
        return redirect("librarian")
    elif patrons.exists():
        return redirect("patron")
    else:
        new_patron = Patron.objects.create(
            user=curr_user,
            name=curr_user.email,
            google_account=curr_user.email,
            date_joined=timezone.now()
        )
        return redirect("patron")

class CollectionsFrontView(ListView):
    template_name = "music/collections_page.html"
    context_object_name = "items"

    def get_queryset(self):
        """
        Returns items filtered by the selected collection and attributes while ensuring
        that private collections are not visible to unauthorized users.
        """
        collection_id = self.request.GET.get("collection")
        curr_user = self.request.user
        user_type = get_user_type(curr_user)

        # Start by fetching all items
        items = Item.objects.all()

        # Collection-based filtering
        if collection_id:
            collection = get_object_or_404(Collection, id=collection_id)

            # Check if the user can access the collection
            if collection.public or user_type == "Librarian" or (
                    user_type == "Patron" and collection.is_accessible_by(curr_user)
            ):
                items = collection.items.all()  # Limit to items in the selected collection
            else:
                return redirect("unauthorized_collection", collection_id=collection.id)

        # Exclude items in private collections that the user cannot access
        else:
            if user_type == "Patron":
                accessible_collections = Collection.objects.filter(
                    Q(public=True) | Q(private_users__user=curr_user)
                )
                items = items.filter(
                    Q(collections__in=accessible_collections) | Q(collections=None)
                ).distinct()
            elif user_type != "Librarian":  # Non-logged-in users
                items = items.filter(
                    Q(collections__public=True) | Q(collections=None)
                ).distinct()

        # Attribute-based filtering
        title = self.request.GET.get("title", "").strip()
        if title:
            items = items.filter(title__icontains=title)

        media_type = self.request.GET.get("media_type", "").strip()
        if media_type:
            items = items.filter(media_type__icontains=media_type)

        description = self.request.GET.get("description", "").strip()
        if description:
            items = items.filter(description__icontains=description)

        status = self.request.GET.get("status", "").strip()
        if status:
            items = items.filter(status=status)  # Exact match for "status"

        # Attach file URLs for the filtered items
        for item in items:
            if item.image:
                item.file_url = aws.generate_url(item.image.name, os.environ.get('BUCKET_NAME'))

        return items

    def get_context_data(self, **kwargs):
        """
        Add all collections with accessibility info and other relevant context data.
        """
        context = super().get_context_data(**kwargs)
        curr_user = self.request.user
        user_type = get_user_type(curr_user)

        # Annotate all collections with access information
        all_collections = Collection.objects.all()
        for collection in all_collections:
            collection.accessible = (
                    collection.public or
                    user_type == 'Librarian' or
                    (user_type == 'Patron' and collection.is_accessible_by(curr_user))
            )

        context["collections"] = all_collections
        collection_id = self.request.GET.get("collection")
        if collection_id:
            context["active_collection"] = get_object_or_404(Collection, id=collection_id)
        else:
            context["active_collection"] = None

        context["user_type"] = user_type
        context["filter_form"] = FilterForm()
        return context


@login_required
def unauthorized_collection_view(request, collection_id):
    """
    Handles unauthorized access and actions for requesting or canceling access.
    """
    collection = get_object_or_404(Collection, id=collection_id)
    user = request.user
    user_type = get_user_type(user)

    if user_type != "Patron":
        return redirect("collections")

    # Determine if the user has already requested access to this collection
    access_requested = collection.pending_users.filter(user=user).exists()

    if request.method == "POST":
        action = request.POST.get("action")

        # Action: "Request Access"
        if action == "request_access" and not access_requested:
            try:
                patron = Patron.objects.get(user=user)
                collection.pending_users.add(patron)
                collection.save()
                messages.success(request, "Your access request has been submitted.")
                access_requested = True  # Update flag
            except Patron.DoesNotExist:
                messages.error(request, "You must be a registered Patron to request access.")

        elif action == "cancel_request" and access_requested:
            try:
                patron = Patron.objects.get(user=user)
                collection.pending_users.remove(patron)
                collection.save()
                messages.success(request, "Your access request has been canceled.")
                access_requested = False  # Update flag
            except Patron.DoesNotExist:
                messages.error(request, "You are not a registered Patron.")

    return render(
        request,
        "music/unauthorized_access.html",
        {"collection": collection, "access_requested": access_requested},
    )


class ItemDetailView(DetailView):
    model = Item
    template_name = "music/item_detail.html"
    context_object_name = "item"

    def get_object(self):
        """
        Fetches the item based on its primary key (id).
        """
        return get_object_or_404(Item, id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        """
        Add item data
        """
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)

        context = super().get_context_data(**kwargs)
        item = self.get_object()

        if item.image:
            file_url = aws.generate_url(item.image.name, os.environ.get('BUCKET_NAME'))
            context['file_url'] = file_url
        else:
            context['file_url'] = None

        context['user_type'] = user_type

        return context

@login_required
def librarian_page(request):
    curr_user = get_user(request)
    librarian = Librarian.objects.filter(user=curr_user).first()

    if librarian.profile_picture:
        file_url = aws.generate_url(librarian.profile_picture.name, os.environ.get('BUCKET_NAME'))
    else:
        file_url = None

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

    if patron.profile_picture:
        file_url = aws.generate_url(patron.profile_picture.name, os.environ.get('BUCKET_NAME'))
    else:
        file_url = None

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

    if patron.profile_picture:
        file_url = aws.generate_url(patron.profile_picture.name, os.environ.get('BUCKET_NAME'))
    else:
        file_url = None

    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=patron)
        if form.is_valid():
            form.save()
            success_message = "Changes saved successfully!"  # Set the success message
            if patron.profile_picture:
                file_url = aws.generate_url(patron.profile_picture.name, os.environ.get('BUCKET_NAME'))
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

    if librarian.profile_picture:
        file_url = aws.generate_url(librarian.profile_picture.name, os.environ.get('BUCKET_NAME'))
    else:
        file_url = None

    if request.method == 'POST':
        form = LibrarianSettingsForm(request.POST, request.FILES, instance=librarian)
        if form.is_valid():
            form.save()
            success_message = "Changes saved successfully!"
            if librarian.profile_picture:
                file_url = aws.generate_url(librarian.profile_picture.name, os.environ.get('BUCKET_NAME'))
            return render(request, 'music/librarian_settings.html',
                          {
                              'form': form,
                              'librarian_first_name': librarian.user.first_name,
                              'librarian_profile_picture': librarian.profile_picture,
                              'librarian_profile_picture_url': file_url,
                              'librarian_bio': librarian.bio,
                              'librarian_birthday': librarian.birthday,
                              'success_message': success_message,
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
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    if request.method == 'POST':
        collection_form = CollectionForm(request.POST)
        item_form = ItemForm(request.POST, request.FILES)

        if "submit_collection" in request.POST:  # User is submitting a Collection
            if collection_form.is_valid():
                title = collection_form.cleaned_data['title']
                if Collection.objects.filter(title__iexact=title).exists():  # Check for duplicate title
                    messages.error(request, f"A Collection with the title '{title}' already exists.")
                else:
                    collection_form.save()
                    return redirect('collections')
            else:
                messages.error(request, "There was an error creating the collection. Please check the form.")

        if "submit_item" in request.POST:  # User is submitting an Item
            if item_form.is_valid():
                description = item_form.cleaned_data['description']

                in_public = False
                in_private = False
                num_private_collections = 0
                for collection in item_form.cleaned_data['collections']:
                    if not collection.public:
                        in_private = True
                        num_private_collections += 1
                    else:
                        in_public = True

                if not description.strip():  # Ensure description is not empty
                    messages.error(request, "Item description cannot be empty.")
                elif in_public and in_private:
                    messages.error(request, "Item cannot be in both a private and public collection.")
                elif num_private_collections > 1:
                    messages.error(request, "Item cannot be in more than one private collection.")
                else:
                    new_item = item_form.save(commit=False)
                    new_item.owner = curr_user
                    new_item.save()
                    new_item.collections.set(item_form.cleaned_data['collections'])
                    new_item.save()
                    return redirect('collections')
            else:
                messages.error(request, "Failed to create the item. Please upload an image in .jpg, .jpeg, or .png format.")

    else:
        collection_form = CollectionForm()
        item_form = ItemForm()

    context = {
        'collection_form': collection_form,
        'item_form': item_form,
        'all_patrons': Patron.objects.all(),
        'all_collections': Collection.objects.all(),
        'media_type': Item.MEDIA_TYPE_CHOICES,
        'status': Item.STATUS_CHOICES,
    }
    return render(request, 'music/create_collection_item.html', context)

@login_required
def manage_collections(request):
    """
    View to display all collections for management.
    """
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    collections = Collection.objects.all()
    return render(request, "music/manage_collections.html", {"collections": collections})

@login_required
def edit_collection(request, title, collection_id):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    collection_title = Collection.objects.get(id=collection_id).title

    # Redirect non-authenticated users and non-Librarians
    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    collection = get_object_or_404(Collection, id=collection_id)

    # Form initialization
    collection_form = CollectionForm(instance=collection)

    if request.method == 'POST':
        collection_form = CollectionForm(request.POST, instance=collection)

        if "submit_collection" in request.POST:  # User is editing the Collection
            if collection_form.is_valid():
                title = collection_form.cleaned_data['title']
                if Collection.objects.filter(title__iexact=title).exists():  # Check for duplicate titles
                    messages.error(request, f"A Collection with the title '{title}' already exists.")
                else:
                    collection_form.save()
                    return redirect('manage_collections')  # Redirect to dashboard or list
            else:
                messages.error(request, "There was an error updating the collection. Please check the form.")

    context = {
        'collection_form': collection_form,
        'collection': collection,
        'all_patrons': Patron.objects.all(),
    }
    return render(request, 'music/edit_collection.html', context)

def delete_collection(request, title, collection_id):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    collection = get_object_or_404(Collection, Q(id=collection_id))

    if request.method == "POST":
        collection.delete()
        return redirect('manage_collections')

    return render(request, 'music/delete_collection.html', {'collection': collection})


@login_required
def view_private_collection_requests(request, collection_id):
    """
    View to display and manage pending user requests for a private collection.
    """
    patrons = Patron.objects.all()

    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    collection = get_object_or_404(Collection, id=collection_id)

    if not collection.public:
        pending_users = collection.pending_users.all()

        if request.method == "POST":
            action = request.POST.get("action")

            if action == "approve_all":
                # Approve all pending users
                for user in pending_users:
                    collection.pending_users.remove(user)
                    collection.private_users.add(user)

            elif action == "deny_all":
                # Deny all pending users
                for user in pending_users:
                    collection.pending_users.remove(user)

            elif action in ["approve", "deny"]:
                user_id = request.POST.get("user_id")
                user = get_object_or_404(Patron, id=user_id)

                if action == "approve":
                    collection.pending_users.remove(user)
                    collection.private_users.add(user)
                elif action == "deny":
                    collection.pending_users.remove(user)

            return redirect('view_requests', collection_id=collection.id)

        return render(request, "music/private_collection_request.html", {
            "collection": collection,
            "pending_users": pending_users,
            "patrons": patrons,
        })

@login_required
def all_private_requests(request):
    """
    View to display all private collections with pending user requests.
    """
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if user_type != "Librarian":
        return redirect("patron")

    # Fetch all private collections with pending users
    private_collections_with_requests = Collection.objects.filter(public=False).filter(pending_users__isnull=False).distinct()

    return render(request, "music/all_private_requests.html", {
        "private_collections_with_requests": private_collections_with_requests,
    })

class ItemEditView(UpdateView):
    model = Item
    fields = ['title', 'description', 'status', 'location', 'media_type', 'image', 'collections', 'tags']
    template_name = "music/item_edit.html"
    context_object_name = "item"

    def get_success_url(self):
        return reverse_lazy('item_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        description = form.cleaned_data['description']
        image = form.cleaned_data.get('image')
        allowed_extensions = ['jpg', 'jpeg', 'png']

        in_public = False
        in_private = False
        num_private_collections = 0

        for collection in form.cleaned_data['collections']:
            if not collection.public:
                in_private = True
                num_private_collections += 1
            else:
                in_public = True

        if not description.strip():
            form.add_error('description', "Item description cannot be empty.")
            messages.error(self.request, "Error: Item description cannot be empty.")
            return self.form_invalid(form)
        elif in_public and in_private:
            form.add_error('collections', "Item cannot be in both a private and public collection.")
            messages.error(self.request, "Error: Item cannot be in both a private and public collection.")
            return self.form_invalid(form)
        elif num_private_collections > 1:
            form.add_error('collections', "Item cannot be in more than one private collection.")
            messages.error(self.request, "Error: Item cannot be in more than one private collection.")
            return self.form_invalid(form)
        elif image:
            ext = str(image.name).split('.')[-1].lower()
            if ext not in allowed_extensions:
                form.add_error('image', "Invalid file format. Only JPG, JPEG, and PNG are allowed.")
                messages.error(self.request, "Error: Invalid file format. Only JPG, JPEG, and PNG are allowed.")
                return self.form_invalid(form)

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There are errors in the form. Please fix them and try again.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)
        context['user_type'] = user_type
        return context

    def dispatch(self, request, *args, **kwargs):
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)

        if not curr_user.is_authenticated:
            messages.error(request, "You must be logged in to edit an item.")
            return redirect(reverse("login"))
        elif user_type != "Librarian":
            messages.error(request, "You do not have permission to edit this item.")
            return redirect("patron")

        return super().dispatch(request, *args, **kwargs)


class ItemDeleteView(DeleteView):
    model = Item
    template_name = 'music/item_confirm_delete.html'

    def get_success_url(self):
        return reverse('collections')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)
        context['user_type'] = user_type
        context['item'] = self.get_object()

        return context

    def dispatch(self, request, *args, **kwargs):
        curr_user = get_user(self.request)
        user_type = get_user_type(curr_user)

        if not curr_user.is_authenticated:
            return redirect(reverse("login"))
        elif user_type != "Librarian":
            return redirect("patron")

        return super().dispatch(request, *args, **kwargs)


@login_required
def create_collection_patron(request):
    curr_user = request.user  # Get the logged-in user
    user_type = get_user_type(curr_user)
    curr_patron = Patron.objects.filter(user=curr_user).first()

    if user_type != "Patron":
        return redirect("librarian")

    if request.method == 'POST':
        collection_form = CollectionForm(request.POST)

        if collection_form.is_valid():
            title = collection_form.cleaned_data['title']
            # Check for duplicate titles
            if Collection.objects.filter(title__iexact=title).exists():
                messages.error(request, f"A Collection with the title '{title}' already exists.")
                return redirect("create_collection_patron")

            collection = collection_form.save(commit=False)
            collection.creator = curr_patron
            collection.public = True  # Forces the collection to be public

            collection.save()

            return redirect("collections")
        else:
            messages.error(request, "There was an error creating the collection. Please check the form and try again.")

    else:
        collection_form = CollectionForm()

    context = {
        'collection_form': collection_form,
    }
    return render(request, 'music/create_collection_patron.html', context)

@login_required
def manage_collections_patron(request):
    curr_user = request.user
    user_type = get_user_type(curr_user)
    curr_patron = Patron.objects.filter(user=curr_user).first()

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Patron":
        return redirect("librarian")

    # Filter collections based on the creator
    collections = Collection.objects.filter(creator=curr_patron)

    context = {
        "collections": collections,
    }
    return render(request, "music/manage_collections_patron.html", context)


@login_required
def edit_collection_patron(request, title, collection_id):
    """
    View for Patrons to edit collections they created.
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)
    curr_patron = Patron.objects.filter(user=curr_user).first()

    collection_title = Collection.objects.get(id=collection_id).title

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Patron":
        return redirect("patron")

    collection = get_object_or_404(Collection, title=collection_title, creator=curr_patron)

    collection_form = CollectionForm(instance=collection)

    if request.method == 'POST':
        collection_form = CollectionForm(request.POST, instance=collection)

        if "submit_collection" in request.POST:
            if collection_form.is_valid():
                title = collection_form.cleaned_data['title']
                if Collection.objects.filter(title__iexact=title).exists():  # Check for duplicate titles
                    messages.error(request, f"A Collection with the title '{title}' already exists.")
                else:
                    collection.public = True  # Forces the collection to be public
                    collection_form.save()
                    return redirect('manage_collections_patron')
            else:
                messages.error(request, "There was an error updating the collection. Please check the form.")

    context = {
        'collection_form': collection_form,
        'collection': collection,
    }
    return render(request, 'music/edit_collection_patron.html', context)


@login_required
def delete_collection_patron(request, title, collection_id):
    """
    View for Patrons to delete collections they created.
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)
    curr_patron = Patron.objects.filter(user=curr_user).first()

    collection_title = Collection.objects.get(id=collection_id).title

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Patron":
        return redirect("patron")

    original_title = title.replace('-', ' ')
    collection = get_object_or_404(Collection, title=collection_title, creator=curr_patron)

    if request.method == "POST":
        collection.delete()
        return redirect('manage_collections_patron')  # Redirect to Patron's collections page

    return render(request, 'music/delete_collection_patron.html', {'collection': collection})

@login_required
def borrow_redir(request, pk):
    item = Item.objects.filter(pk=pk).first()
    owner = item.owner
    print(owner.first_name)
    requester = get_user(request)
    print(requester.first_name)
    print(owner.pk)

    if(owner.email == requester.email):
        messages.error(request, "ERROR: Cannot request your own item!")
        return redirect("item_detail", pk)
    if(BorrowRequest.objects.filter(item_owner=owner, requester=requester, requested_item=item).exists()):
        messages.error(request, "ERROR: You have already requested this item! Please wait to be approved.")
        return redirect("item_detail", pk)
    
    borrow_request = BorrowRequest(requested_item=item, item_owner=owner, requester=requester)
    borrow_request.save()
    
    messages.success(request, "Success! Your request has been sent.")
    return redirect("item_detail", pk)

def incoming_requests(request):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    incoming_list = BorrowRequest.objects.filter(item_owner=curr_user)
    print(incoming_list)

    return render(request, "music/incoming_borrow_requests.html", {
        "incoming_list": incoming_list, 
        })

def approve_request(request, borrow_request_id):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")
    
    borrow_request = BorrowRequest.objects.filter(pk=borrow_request_id).first()
    borrow_request.status = "APPROVED"
    borrow_request.save()

    return redirect("incoming_requests")
    
def deny_request(request, borrow_request_id):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")   

    borrow_request = BorrowRequest.objects.filter(pk=borrow_request_id).first()
    borrow_request.status = "DENIED"
    borrow_request.save()

    return redirect("incoming_requests")   

def outgoing_requests(request):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))

    outgoing_list = BorrowRequest.objects.filter(requester=curr_user)
    return render(request, "music/outgoing_borrow_requests.html", {
        "outgoing_list": outgoing_list, 
        "user_type": user_type,
        })