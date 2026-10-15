from collections import defaultdict

from django.shortcuts import render
from django.views import View

from movies.models import Movie, Watchlist


class RecommendationView(View):
    template_name = 'recommendations/index.html'

    def get(self, request):
        watchlisted_ids = set()

        if request.user.is_authenticated and not request.user.is_new_user:
            from .engine import get_recommendations
            # Keep the engine's personalised order (don't re-sort by avg_rating)
            recommendations = get_recommendations(request.user.id, n=20)

            # Group by primary genre, pick top 4 most-populated genres
            genre_groups = defaultdict(list)
            for movie in recommendations:
                genres = list(movie.genres.all())
                primary = genres[0].name if genres else 'Other'
                genre_groups[primary].append(movie)

            genre_sections = sorted(genre_groups.items(), key=lambda x: len(x[1]), reverse=True)[:4]

            all_movie_ids = [m.pk for movies in genre_groups.values() for m in movies]
            if all_movie_ids:
                watchlisted_ids = set(
                    Watchlist.objects.filter(
                        user=request.user, movie_id__in=all_movie_ids
                    ).values_list('movie_id', flat=True)
                )

            context = {
                'genre_sections': genre_sections,
                'is_cold_start': False,
                'watchlisted_ids': watchlisted_ids,
            }
        else:
            trending = list(Movie.objects.order_by('-total_watches').prefetch_related('genres')[:12])
            top_rated = list(Movie.objects.order_by('-avg_rating').prefetch_related('genres')[:12])
            new_releases = list(Movie.objects.order_by('-year', '-avg_rating').prefetch_related('genres')[:12])

            if request.user.is_authenticated:
                all_ids = {m.pk for m in trending + top_rated + new_releases}
                watchlisted_ids = set(
                    Watchlist.objects.filter(
                        user=request.user, movie_id__in=all_ids
                    ).values_list('movie_id', flat=True)
                )

            context = {
                'trending': trending,
                'top_rated': top_rated,
                'new_releases': new_releases,
                'is_cold_start': True,
                'watchlisted_ids': watchlisted_ids,
            }
        return render(request, self.template_name, context)
