from django import forms
from .models import Patron, Librarian, Collection, Item, Comment, Rating

class SettingsForm(forms.ModelForm):
    class Meta:
        model = Patron
        fields = ['profile_picture', 'bio', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'style': 'height: 150px;'})
        }

class LibrarianSettingsForm(forms.ModelForm):
    class Meta:
        model = Librarian
        fields = ['profile_picture', 'bio', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'bio': forms.Textarea(attrs={'style': 'height: 150px;'})
        }

class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['title', 'description', 'public', 'private_users']

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['title', 'description', 'status', 'location', 'media_type', 'image', 'collections', 'tags', 'genre']

    def clean_collections(self):
        collections = self.cleaned_data.get('collections')
        return collections

class FilterForm(forms.Form):
    title = forms.CharField(label="Title", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    media_type = forms.ChoiceField(
        label="Media Type",
        required=False,
        choices=[
            ("CD", "CD"),
            ("VINYL", "Vinyl"),
            ("BLU_RAY", "Blu-ray"),
            ("CASSETTE", "Cassette"),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    description = forms.CharField(label="Description", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    availability = forms.ChoiceField(
        label="Availability",
        required=False,
        choices=[
            ("CHECKED_IN", "Checked In"),
            ("IN_CIRCULATION", "In Circulation"),
            ("BEING_REPAIRED", "Being Repaired"),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    genre = forms.CharField(label="Genre", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tags = forms.CharField(label="Tags", required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a comment...',
                'maxlength': 200,  # HTML-level limit
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) > 200:
            raise forms.ValidationError("Comment cannot exceed 200 characters.")
        return text


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.RadioSelect(choices=[(i, f'{i} ★') for i in range(1, 6)])
        }