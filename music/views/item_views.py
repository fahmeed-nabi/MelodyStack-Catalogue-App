from django.contrib import messages
from django.contrib.auth import get_user
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, DeleteView, UpdateView

from music import aws
from music.models import Librarian, Patron, Item, BorrowRequest
from music.utils import get_user_type
from mysite.settings import os.environ.get('BUCKET_NAME')


class ItemDetailView(DetailView):
    model = Item
    template_name = "music/item_detail.html"
    context_object_name = "item"

    def get_object(self):
        return get_object_or_404(Item, id=self.kwargs.get('pk'))

    def get_context_data(self, **kwargs):
        curr_user = self.request.user
        user_type = get_user_type(curr_user)

        context = super().get_context_data(**kwargs)
        item = self.get_object()

        # Check if the current user has already saved this item
        already_saved = False
        if user_type == "Patron":
            patron = Patron.objects.filter(user=curr_user).first()
            if patron and item in patron.saved_items.all():
                already_saved = True
        elif user_type == "Librarian":
            librarian = Librarian.objects.filter(user=curr_user).first()
            if librarian and item in librarian.saved_items.all():
                already_saved = True

        # Check if the current user has already requested this item
        already_requested = False
        denied = False

        if user_type in ["Patron", "Librarian"]:  # Only check if user is valid
            pending_requests = BorrowRequest.objects.filter(
                requested_item=item,
                requester=curr_user,
                status="PENDING"
            )
            denied_requests = BorrowRequest.objects.filter(
                requested_item=item,
                requester=curr_user,
                status="DENIED"
            )

            already_requested = pending_requests.exists()
            denied = denied_requests.exists()

        context.update({
            'file_url': aws.generate_url(item.image.name, os.environ.get('BUCKET_NAME')) if item.image else None,
            'user_type': user_type,
            'already_saved': already_saved,
            'already_requested': already_requested,
            'denied': denied,
        })

        return context

    def post(self, request, *args, **kwargs):
        """
        Handles saving and unsaving an item for both Patrons and Librarians.
        """
        item = self.get_object()
        curr_user = request.user
        user_type = get_user_type(curr_user)

        if not curr_user.is_authenticated:
            return JsonResponse({'message': 'You must be logged in to save items.'}, status=403)

        if user_type == "Patron":
            patron = Patron.objects.filter(user=curr_user).first()
            if patron:
                if item in patron.saved_items.all():
                    patron.saved_items.remove(item)
                    message = "Item unsaved successfully."
                else:
                    patron.saved_items.add(item)
                    message = "Item saved successfully."
                patron.save()
            else:
                return JsonResponse({'message': 'Error: Patron not found.'}, status=404)

        elif user_type == "Librarian":
            librarian = Librarian.objects.filter(user=curr_user).first()
            if librarian:
                if item in librarian.saved_items.all():
                    librarian.saved_items.remove(item)
                    message = "Item unsaved successfully."
                else:
                    librarian.saved_items.add(item)
                    message = "Item saved successfully."
                librarian.save()
            else:
                return JsonResponse({'message': 'Error: Librarian not found.'}, status=404)

        else:
            return JsonResponse({'message': 'Invalid user type.'}, status=400)

        return JsonResponse({'message': message})


class ItemEditView(UpdateView):
    model = Item
    fields = ['title', 'description', 'status', 'location', 'media_type', 'image', 'collections', 'tags']
    template_name = "music/item_edit.html"
    context_object_name = "item"

    def get_success_url(self):
        return reverse_lazy('item_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Validation logic remains unchanged
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

        # Add current title and description lengths to context
        item = self.object
        context['current_title_remaining'] = 100 - len(item.title) if item.title else 0
        context['current_description_remaining'] = 500 - len(item.description) if item.description else 0

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
def borrow_redir(request, pk):
    """
    Handles borrowing requests by adding the user to the requesters list.
    """
    item = get_object_or_404(Item, pk=pk)
    requester = request.user  # Use Django's built-in user system

    # Get or create a borrow request for this item
    borrow_request, created = BorrowRequest.objects.get_or_create(requested_item=item, requester=requester)

    if not created:
        messages.error(request, "ERROR: You have already requested this item! Please wait to be approved.")
        return redirect("item_detail", pk=pk)

    borrow_request.save()
    messages.success(request, "Success! Your request has been sent.")
    return redirect("item_detail", pk=pk)

@login_required
def saved_items_view(request):
    curr_user = request.user
    user_type = get_user_type(curr_user)

    if user_type == 'Patron':
        patron = Patron.objects.filter(user=curr_user).first()
        saved_items = patron.saved_items.all() if patron else []
    elif user_type == 'Librarian':
        librarian = Librarian.objects.filter(user=curr_user).first()
        saved_items = librarian.saved_items.all() if librarian else []
    else:
        saved_items = []

    for item in saved_items:
        item.image_url = aws.generate_url(item.image.name, os.environ.get('BUCKET_NAME')) if item.image else None

    return render(request, 'music/saved_items.html', {'saved_items': saved_items, 'user_type': user_type})