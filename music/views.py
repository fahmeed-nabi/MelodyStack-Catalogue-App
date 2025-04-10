from django.contrib.auth import get_user_model

User = get_user_model()

"""
NOTE: views were restructured so that functionality is now organized into separate modules within
the music/views/ directory. Each view group (e.g., auth, patron, librarian, etc.) has its own file for
better maintainability. Please refer to the music/views/ folder for the view implementations or to
include your views.
"""


