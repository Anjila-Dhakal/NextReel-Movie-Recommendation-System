from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Movie(models.Model):
    title = models.CharField(max_length=300)
    genres = models.ManyToManyField(Genre, blank=True)
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, default='')
    poster = models.ImageField(upload_to='movies/posters/', null=True, blank=True)
    poster_url_external = models.URLField(max_length=500, blank=True, default='')
    movielens_id = models.IntegerField(unique=True, null=True, blank=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    avg_rating = models.FloatField(default=0.0)
    total_ratings = models.IntegerField(default=0)
    total_watches = models.IntegerField(default=0)

    class Meta:
        ordering = ['-avg_rating']

    def __str__(self):
        return self.title

    @property
    def poster_url(self):
        if self.poster and self.poster.name:
            return self.poster.url
        if self.poster_url_external:
            return self.poster_url_external
        return '/static/images/default_poster.svg'

    def get_star_range(self):
        """Returns list of (index, filled) tuples for rendering 5 stars."""
        rating = round(self.avg_rating)
        return [(i, i <= rating) for i in range(1, 6)]


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} -> {self.movie.title}"


class WatchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_history')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watched_by')
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-watched_at']

    def __str__(self):
        return f"{self.user.username} watched {self.movie.title}"
