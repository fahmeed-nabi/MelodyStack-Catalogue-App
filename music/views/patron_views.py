from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from music import aws
from music.forms import SettingsForm, CollectionForm
from music.models import Patron, Collection, Item
from music.utils import get_user_type
from mysite.settings import os.environ.get('BUCKET_NAME')


@login_required
def patron_page(request):
    curr_user = get_user(request)
    user_type = get_user_type(curr_user)

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Patron":
        return redirect("librarian")

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
def create_collection_patron(request):
    curr_user = request.user  # Get the logged-in user
    user_type = get_user_type(curr_user)
    curr_patron = Patron.objects.filter(user=curr_user).first()

    if not request.user.is_authenticated:
        return redirect(reverse("login"))
    elif user_type != "Patron":
        return redirect("librarian")

    # Fetch items that are not in any private collection
    available_items = Item.objects.filter(~Q(collections__public=False)).distinct()

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

            # Add selected items to the collection
            item_ids = request.POST.getlist('items')  # Get selected item IDs from the form
            selected_items = Item.objects.filter(id__in=item_ids)
            collection.items.add(*selected_items)

            return redirect("collections")
        else:
            messages.error(request, "There was an error creating the collection. Please check the form and try again.")

    else:
        collection_form = CollectionForm()

    context = {
        'collection_form': collection_form,
        'available_items': available_items,  # Pass available items to the template
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
        return redirect("librarian")

    collection = get_object_or_404(Collection, title=collection_title, creator=curr_patron)

    # Fetch items that are not in any private collections
    available_items = Item.objects.filter(~Q(collections__public=False)).distinct()

    collection_form = CollectionForm(instance=collection)

    if request.method == 'POST':
        collection_form = CollectionForm(request.POST, instance=collection)

        if "submit_collection" in request.POST:
            if collection_form.is_valid():
                title = collection_form.cleaned_data['title']
                title_query = Collection.objects.filter(title__iexact=title)
                if title_query.exists() and title_query.first().id != collection.id:  # Check for duplicate titles
                    messages.error(request, f"A Collection with the title '{title}' already exists.")
                else:
                    collection.public = True  # Forces the collection to be public
                    collection_form.save()

                    # Update items in the collection
                    item_ids = request.POST.getlist('items')  # Get selected item IDs from the form
                    selected_items = Item.objects.filter(id__in=item_ids)
                    collection.items.set(selected_items)  # Replace existing items with selected ones

                    return redirect('manage_collections_patron')
            else:
                messages.error(request, "There was an error updating the collection. Please check the form.")

    context = {
        'collection_form': collection_form,
        'collection': collection,
        'available_items': available_items,
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
        return redirect("librarian")

    original_title = title.replace('-', ' ')
    collection = get_object_or_404(Collection, title=collection_title, creator=curr_patron)

    if request.method == "POST":
        collection.delete()
        return redirect('manage_collections_patron')  # Redirect to Patron's collections page

    return render(request, 'music/delete_collection_patron.html', {'collection': collection})