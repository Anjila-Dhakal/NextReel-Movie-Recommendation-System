
from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'rating-input',
            'min': 1,
            'max': 5,
        }),
    )

    class Meta:
        model = Review
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Share your thoughts...',
                'rows': 5,
            }),
        }

    def clean_review_text(self):
        text = self.cleaned_data['review_text'].strip()

        # Reject empty review
        if not text:
            raise forms.ValidationError(
                "Please enter a review."
            )

        # Reject numbers/symbols only
        if not any(char.isalpha() for char in text):
            raise forms.ValidationError(
                "Please enter a valid text review, not numbers only."
            )

        return text

