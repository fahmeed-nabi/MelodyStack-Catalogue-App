from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from music import aws
from music.forms import LibrarianSettingsForm, CollectionForm, ItemForm
from music.models import Librarian, Patron, Collection, Item, BorrowRequest
from music.utils import get_user_type
from mysite.settings import os.environ.get('BUCKET_NAME')

@login_required
def librarian_page(request):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

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
def patron_promotion_view(request):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    context = {
        'all_patrons': Patron.objects.all(),
    }
    return render(request, 'music/promote_patron.html', context)


def patron_promotion_confirmation(request, patron_id):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Librarian":
        return redirect("patron")

    patron = get_object_or_404(Patron, Q(id=patron_id))

    if request.method == "POST":
        collections = Collection.objects.all()
        for collection in collections:
            if collection.is_accessible_by(patron.user):
                collection.creator = None
                collection.save()
        librarian = Librarian(user=patron.user, name=patron.name, google_account=patron.google_account,
                              profile_picture=patron.profile_picture, date_joined=patron.date_joined, bio=patron.bio,
                              birthday=patron.birthday)
        librarian.save()
        patron.delete()
        return redirect("promote_patron")

    return render(request, 'music/promote_patron_confirmation.html', {'patron': patron})

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


@login_required
def incoming_requests(request):
    """
    Shows incoming borrow requests for the logged-in user (only librarians).
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    if user_type != "Librarian":
        return redirect("patron")

    # Fetch all borrow requests where the user is the owner
    incoming_list = BorrowRequest.objects.all()

    return render(request, "music/incoming_borrow_requests.html", {
        "incoming_list": incoming_list,
    })


@login_required
def approve_request(request, borrow_request_id, user_id):
    """
    Approves a borrow request for a specific user.
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    if user_type != "Librarian":
        return redirect("patron")

    borrow_request = get_object_or_404(BorrowRequest, pk=borrow_request_id)
    requests_to_item = BorrowRequest.objects.filter(requested_item=borrow_request.requested_item)

    for r in requests_to_item:
        r.status = "DENIED"
        r.save()
    borrow_request.status = 'APPROVED'
    borrow_request.save()
    item = borrow_request.requested_item
    item.status = 'IN_CIRCULATION'
    item.due_date = timezone.now() + timezone.timedelta(days=7)
    item.save()
    messages.success(request, f"Borrow request for {borrow_request.requester.first_name} has been approved.")

    return redirect("incoming_requests")


@login_required
def deny_request(request, borrow_request_id, user_id):
    """
    Denies a borrow request for a specific user.
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    if user_type != "Librarian":
        return redirect("patron")

    borrow_request = get_object_or_404(BorrowRequest, pk=borrow_request_id)

    borrow_request.status = 'DENIED'
    borrow_request.save()
    messages.warning(request, f"Borrow request for {borrow_request.requester.first_name} has been denied.")

    return redirect("incoming_requests")


@login_required
def outgoing_requests(request):
    """
    Shows borrow requests made by the logged-in user.
    """
    curr_user = request.user
    user_type = get_user_type(curr_user)

    outgoing_list = BorrowRequest.objects.filter(requester=curr_user)
    for outgoing_request in outgoing_list:
        if (timezone.now().date() > outgoing_request.requested_item.due_date and outgoing_request.status == "APPROVED"):
            outgoing_request.status = 'OVERDUE'
            outgoing_request.save()

    # Find borrow requests where the user is in the requesters list
    # outgoing_list = BorrowRequest.objects.filter(requesters=curr_user)

    return render(request, "music/outgoing_borrow_requests.html", {
        "outgoing_list": outgoing_list,
        "user_type": user_type,
    })


@login_required
def return_redir(request, pk):
    curr_user = request.user
    user_type = get_user_type(curr_user)

    # On an item's return, we want to update the item to be no longer borrowed, delete all borrow requests relating to an item, and display a message saying that the item was returned successfully

    borrow_request = BorrowRequest.objects.filter(pk=pk).first()
    item = borrow_request.requested_item

    item.status = 'CHECKED_IN'
    item.save()

    BorrowRequest.objects.filter(requested_item=item).delete()
    messages.success(request, f"{borrow_request.requested_item.title} has been successfully returned")

    return redirect(reverse("outgoing_requests"))