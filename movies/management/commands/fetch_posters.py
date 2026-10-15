"""
Usage: python manage.py fetch_posters --api-key YOUR_TMDB_API_KEY

Fetches poster URLs from TMDB for all movies missing a poster.
Matches by title + year using the TMDB search API.
Stores the URL in Movie.poster_url_external (no download needed).
"""
import re
import time

import requests
from django.core.management.base import BaseCommand

from movies.models import Movie

TMDB_SEARCH_URL = 'https://api.themoviedb.org/3/search/movie'
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'


def clean_title(title):
    """Convert MovieLens title format to a clean searchable title.
    - Strips parenthetical subtitles/alternates: 'Foo (Bar)' -> 'Foo'
    - Moves trailing articles: 'Decalogue, The' -> 'The Decalogue'
    """
    # Remove anything in parentheses (alternate/foreign titles)
    t = re.sub(r'\s*\([^)]*\)', '', title).strip()
    # Move trailing article: "Title, The" -> "The Title"
    t = re.sub(r'^(.*),\s*(The|A|An)$', r'\2 \1', t, flags=re.IGNORECASE)
    return t.strip()


class Command(BaseCommand):
    help = 'Fetch poster URLs from TMDB for all movies missing posters'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=True, help='TMDB API key (v3)')
        parser.add_argument('--overwrite', action='store_true', help='Re-fetch even if poster already exists')
        parser.add_argument('--limit', type=int, default=None, help='Limit number of movies to process (for testing)')

    def handle(self, *args, **options):
        api_key = options['api_key']
        overwrite = options['overwrite']
        limit = options['limit']

        movies = Movie.objects.all()
        if not overwrite:
            movies = movies.filter(poster_url_external='').filter(
                poster__in=['', None]
            )

        if limit:
            movies = movies[:limit]

        total = movies.count()
        self.stdout.write(f'Fetching posters for {total} movies...')

        found = 0
        not_found = 0
        errors = 0

        for i, movie in enumerate(movies, 1):
            try:
                search_title = clean_title(movie.title)
                params = {
                    'api_key': api_key,
                    'query': search_title,
                    'language': 'en-US',
                    'page': 1,
                    'include_adult': False,
                }
                if movie.year:
                    params['year'] = movie.year

                resp = requests.get(TMDB_SEARCH_URL, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                poster_path = None
                results = data.get('results', [])

                # Try exact year match first, then fallback to first result
                if results:
                    for result in results[:3]:
                        release = result.get('release_date', '')
                        result_year = int(release[:4]) if release and len(release) >= 4 else None
                        if result_year == movie.year and result.get('poster_path'):
                            poster_path = result['poster_path']
                            break
                    if not poster_path and results[0].get('poster_path'):
                        poster_path = results[0]['poster_path']

                if poster_path:
                    movie.poster_url_external = TMDB_IMAGE_BASE + poster_path
                    movie.save(update_fields=['poster_url_external'])
                    found += 1
                else:
                    not_found += 1

                # Progress update every 100 movies
                if i % 100 == 0:
                    self.stdout.write(f'  {i}/{total} processed — {found} found, {not_found} not found so far')

                # Respect TMDB rate limit (40 requests/10s)
                time.sleep(0.26)

            except requests.exceptions.RequestException as e:
                errors += 1
                if errors <= 5:
                    self.stderr.write(f'  Error fetching "{movie.title}": {e}')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Found: {found}, Not found: {not_found}, Errors: {errors}'
        ))
