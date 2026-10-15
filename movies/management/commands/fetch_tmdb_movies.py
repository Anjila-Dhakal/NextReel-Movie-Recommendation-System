"""
Fetch popular, top-rated, and now-playing movies from TMDB and save them to the database.

Usage:
    python manage.py fetch_tmdb_movies
    python manage.py fetch_tmdb_movies --pages 5
    python manage.py fetch_tmdb_movies --lists popular top_rated now_playing upcoming

Requires TMDB_API_KEY in settings or environment.
"""
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from movies.models import Genre, Movie

TMDB_BASE = 'https://api.themoviedb.org/3'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'

TMDB_GENRE_MAP = {
    28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy',
    80: 'Crime', 99: 'Documentary', 18: 'Drama', 10751: 'Family',
    14: 'Fantasy', 36: 'History', 27: 'Horror', 10402: 'Music',
    9648: 'Mystery', 10749: 'Romance', 878: 'Sci-Fi', 10770: 'TV Movie',
    53: 'Thriller', 10752: 'War', 37: 'Western',
}


class Command(BaseCommand):
    help = 'Fetch latest movies from TMDB API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages', type=int, default=3,
            help='Number of pages to fetch per list (20 movies per page)',
        )
        parser.add_argument(
            '--lists', nargs='+',
            default=['popular', 'top_rated', 'now_playing', 'upcoming'],
            choices=['popular', 'top_rated', 'now_playing', 'upcoming'],
            help='Which TMDB lists to fetch',
        )

    def handle(self, *args, **options):
        api_key = getattr(settings, 'TMDB_API_KEY', '') or ''
        if not api_key:
            raise CommandError(
                'TMDB_API_KEY is not set. Add it to settings.py or set the '
                'TMDB_API_KEY environment variable. Get a free key at '
                'https://www.themoviedb.org/settings/api'
            )

        pages = options['pages']
        lists = options['lists']
        created_total = 0
        updated_total = 0

        for list_name in lists:
            self.stdout.write(f'Fetching {list_name} ({pages} pages)...')
            movies_data = self._fetch_list(api_key, list_name, pages)
            c, u = self._save_movies(movies_data)
            created_total += c
            updated_total += u
            self.stdout.write(self.style.SUCCESS(
                f'  {list_name}: {c} new, {u} updated'
            ))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. Total new: {created_total}, updated: {updated_total}. '
            f'Total movies in DB: {Movie.objects.count()}'
        ))

    def _fetch_list(self, api_key, list_name, pages):
        movies = []
        for page in range(1, pages + 1):
            url = f'{TMDB_BASE}/movie/{list_name}'
            params = {'api_key': api_key, 'language': 'en-US', 'page': page}
            try:
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                movies.extend(data.get('results', []))
                time.sleep(0.25)  # stay within TMDB rate limit
            except requests.RequestException as e:
                self.stderr.write(self.style.WARNING(f'  Page {page} failed: {e}'))
        return movies

    def _save_movies(self, movies_data):
        created = 0
        updated = 0
        with transaction.atomic():
            for item in movies_data:
                tmdb_id = item.get('id')
                if not tmdb_id:
                    continue

                title = item.get('title') or item.get('original_title', '')
                if not title:
                    continue

                release_date = item.get('release_date', '')
                year = None
                if release_date and len(release_date) >= 4:
                    try:
                        year = int(release_date[:4])
                    except ValueError:
                        pass

                poster_path = item.get('poster_path', '')
                poster_url = f'{TMDB_IMAGE_BASE}{poster_path}' if poster_path else ''

                # TMDB vote_average is out of 10; convert to 5-star scale
                vote_avg = item.get('vote_average', 0) or 0
                avg_rating = round(vote_avg / 2, 2)
                total_ratings = item.get('vote_count', 0) or 0

                description = item.get('overview', '') or ''

                genre_ids = item.get('genre_ids', [])

                movie, created_flag = Movie.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        'title': title,
                        'year': year,
                        'poster_url_external': poster_url,
                        'avg_rating': avg_rating,
                        'total_ratings': total_ratings,
                        'description': description,
                    },
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

                # Set genres
                genre_objs = []
                for gid in genre_ids:
                    genre_name = TMDB_GENRE_MAP.get(gid)
                    if genre_name:
                        genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                        genre_objs.append(genre_obj)
                if genre_objs:
                    movie.genres.set(genre_objs)

        return created, updated
