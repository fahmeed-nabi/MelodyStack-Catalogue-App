from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.contrib import messages

from music import aws
from music.forms import FilterForm
from music.models import Item, Collection, Patron
from music.utils import get_user_type
from mysite.settings import os.environ.get('BUCKET_NAME')

class CollectionsFrontView(ListView):
    template_name = "music/collections_page.html"
    context_object_name = "items"

    def get_queryset(self):
        """
        Returns paginated items filtered by collection and attributes, while ensuring
        that private collections are not visible to unauthorized users.
        """
        collection_id = self.request.GET.get("collection")
        curr_user = self.request.user
        user_type = get_user_type(curr_user)

        items = Item.objects.all()

        # Collection-based filtering
        if collection_id:
            collection = get_object_or_404(Collection, id=collection_id)
            if collection.public or user_type == "Librarian" or (
                user_type == "Patron" and collection.is_accessible_by(curr_user)
            ):
                items = collection.items.all()
            else:
                return redirect("unauthorized_collection", collection_id=collection.id)
        else:
            if user_type == "Patron":
                accessible_collections = Collection.objects.filter(
                    Q(public=True) | Q(private_users__user=curr_user)
                )
                items = items.filter(
                    Q(collections__in=accessible_collections) | Q(collections=None)
                ).distinct()
            elif user_type != "Librarian":
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
            items = items.filter(status=status)

        genre = self.request.GET.get("genre", "").strip()
        if genre:
            items = items.filter(genre__icontains=genre)

        tags = self.request.GET.get("tags", "").strip()
        if tags:
            items = items.filter(tags__icontains=tags)

        # ordered pagination
        items = items.order_by('-created_at')

        # Attach file URLs to items
        for item in items:
            if item.image:
                item.file_url = aws.generate_url(item.image.name, os.environ.get('BUCKET_NAME'))

        # PAGINATION
        paginator = Paginator(items, 9)  # display 9 items per page
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return page_obj

    def get_context_data(self, **kwargs):
        """
        Add all collections with accessibility info and pagination context.
        """
        context = super().get_context_data(**kwargs)
        curr_user = self.request.user
        user_type = get_user_type(curr_user)

        # Annotate collections with access info
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
        context["page_obj"] = context["items"]  # So templates can use pagination controls

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