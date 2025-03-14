from django import forms
from .models import Patron, Librarian

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Patron
        fields = ['profile_picture', 'bio', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),  # Ensures birthday is displayed as a date input
            'bio': forms.Textarea(attrs={'style': 'height: 150px;'})  # Set height for the biography textarea
        }

    # def clean_profile_picture(self):
    #     picture = self.cleaned_data.get('profile_picture')
    #     if picture:
    #         # Example: Check if file type is allowed (e.g., .jpg, .png)
    #         if not picture.name.endswith(('.jpg', '.jpeg', '.png')):
    #             raise forms.ValidationError("Only .jpg, .jpeg, and .png files are allowed.")
    #     return picture
