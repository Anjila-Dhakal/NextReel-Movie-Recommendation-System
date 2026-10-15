from django.contrib import admin

from .models import Genre, Movie, Watchlist, WatchHistory


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'avg_rating', 'total_ratings', 'total_watches', 'movielens_id')
    list_filter = ('genres', 'year')
    search_fields = ('title', 'description')
    filter_horizontal = ('genres',)
    readonly_fields = ('avg_rating', 'total_ratings', 'total_watches')
    ordering = ('-avg_rating',)


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'movie__title')
    raw_id_fields = ('user', 'movie')


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'watched_at')
    list_filter = ('watched_at',)
    search_fields = ('user__username', 'movie__title')
    raw_id_fields = ('user', 'movie')
