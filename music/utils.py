from .models import Patron, Librarian

def get_user_type(user):
    librarians = Librarian.objects.filter(user=user)
    patrons = Patron.objects.filter(user=user)

    if librarians.exists():  # takes precedence over patron
        return 'Librarian'
    elif patrons.exists():
        return 'Patron'
    else:
        return 'Anonymous'