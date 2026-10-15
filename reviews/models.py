from django.db import models
from django.contrib.auth import get_user_model

from movies.models import Movie

User = get_user_model()

SENTIMENT_CHOICES = [
    ('positive', 'Positive'),
    ('negative', 'Negative'),
    ('neutral', 'Neutral'),
]


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review_text = models.TextField()
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, default='neutral')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} ({self.rating}\u2605)"

    def get_star_range(self):
        """Returns list of (index, filled) tuples for rendering 5 stars."""
        return [(i, i <= self.rating) for i in range(1, 6)]
