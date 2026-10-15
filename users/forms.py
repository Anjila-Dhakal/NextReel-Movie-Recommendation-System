
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class RegisterForm(UserCreationForm):

    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Choose a unique username'
            }
        ),
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Email address'
            }
        ),
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'First name'
            }
        ),
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Last name'
            }
        ),
    )

    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Password'
            }
        ),
    )

    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'Confirm password'
            }
        ),
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2'
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        if not username:
            raise forms.ValidationError(
                'Username is required.'
            )

        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'A user with this username already exists.'
            )

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email:
            raise forms.ValidationError(
                'Email address is required.'
            )

        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'A user with this email already exists.'
            )

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()

        # First name is required
        if not first_name:
            raise forms.ValidationError(
                'First name is required.'
            )

        # Letters only
        if not first_name.isalpha():
            raise forms.ValidationError(
                'First name must contain letters only.'
            )

        # Maximum 9 letters
        if len(first_name) > 9:
            raise forms.ValidationError(
                'First name cannot contain more than 9 letters.'
            )

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()

        # Last name is required
        if not last_name:
            raise forms.ValidationError(
                'Last name is required.'
            )

        # Letters only
        if not last_name.isalpha():
            raise forms.ValidationError(
                'Last name must contain letters only.'
            )

        return last_name


class ProfileEditForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'bio',
            'avatar'
        ]

        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'First name'
                }
            ),
            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Last name'
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'Email address'
                }
            ),
            'bio': forms.Textarea(
                attrs={
                    'class': 'form-textarea',
                    'placeholder': 'Tell us about yourself...',
                    'rows': 4
                }
            ),
            'avatar': forms.FileInput(
                attrs={
                    'class': 'form-input'
                }
            ),
        }
