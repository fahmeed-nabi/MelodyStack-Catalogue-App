from django.db.models import QuerySet, Q

from .models import Patron, Librarian, Collection

def get_user_type(user):
    if not user.is_authenticated:
        return 'Anonymous'

    librarians = Librarian.objects.filter(user=user)
    patrons = Patron.objects.filter(user=user)

    if librarians.exists():  # takes precedence over patron
        return 'Librarian'
    elif patrons.exists():
        return 'Patron'
    else:
        return 'Anonymous'


def get_accessible_collections(user) -> QuerySet:
    user_type = get_user_type(user)

    if user_type == 'Librarian':
        return Collection.objects.all()
    elif user_type == 'Patron':
        accessible_collections = [
            collection for collection in Collection.objects.all()
            if collection.is_accessible_by(user)
        ]

        # Convert the list back into a QuerySet
        return Collection.objects.filter(id__in=[col.id for col in accessible_collections])


