from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    bio = models.TextField(blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    theme_preference = models.CharField(
        max_length=10,
        default='dark',
        choices=[('dark', 'Cinematic Dark'), ('warm', 'Warm Glow')],
    )
    is_new_user = models.BooleanField(default=True)  # becomes False after first rating

    def __str__(self):
        return self.username

    def get_avatar_url(self):
        if self.avatar and self.avatar.name:
            return self.avatar.url
        return '/static/images/default_avatar.svg'
