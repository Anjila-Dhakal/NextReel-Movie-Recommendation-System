from django import forms

from .models import Movie


class MovieForm(forms.ModelForm):
    """For admin panel movie management."""

    class Meta:
        model = Movie
        fields = ['title', 'genres', 'year', 'description', 'poster', 'poster_url_external', 'movielens_id']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Movie title'}),
            'year': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Release year'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Movie description...', 'rows': 5}),
            'poster': forms.FileInput(attrs={'class': 'form-input'}),
            'poster_url_external': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://example.com/poster.jpg'}),
            'movielens_id': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'MovieLens ID'}),
            'genres': forms.SelectMultiple(attrs={'class': 'form-input'}),
        }
    def clean_title(self):                                          # ← NAYA METHOD
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise forms.ValidationError('Title is required.')

        if title.isdigit():
            raise forms.ValidationError('Title must contain letters, not just numbers.')

        if not any(char.isalpha() for char in title):
            raise forms.ValidationError('Title must contain at least one letter.')

        return title


class SearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Search movies...'}),
    )
    genre = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )
    year_from = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'From year'}),
    )
    year_to = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'To year'}),
    )
    min_rating = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Min rating', 'step': '0.1', 'min': '0', 'max': '5'}),
    )
