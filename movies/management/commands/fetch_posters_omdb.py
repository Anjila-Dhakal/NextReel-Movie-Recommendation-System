"""
Usage: python manage.py fetch_posters_omdb --api-key YOUR_OMDB_KEY

Fetches and downloads poster images from OMDB for all movies missing posters.
Uses IMDB IDs from datasets/ml-latest-small/links.csv to match movies.
Downloads images to media/movies/posters/ and updates Movie.poster field.
Free OMDB tier: 1,000 requests/day — run daily until all movies are covered.
"""
import os
import re
import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from movies.models import Movie

OMDB_URL = 'http://www.omdbapi.com/'
POSTERS_DIR = os.path.join(settings.MEDIA_ROOT, 'movies', 'posters')


def safe_filename(title):
    name = re.sub(r'[^\w\s-]', '', title).strip()
    name = re.sub(r'\s+', '_', name)
    return name[:50]


class Command(BaseCommand):
    help = 'Fetch and download poster images from OMDB for all movies missing posters'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=True, help='OMDB API key')
        parser.add_argument('--limit', type=int, default=1000, help='Max requests to make (default 1000 = free tier daily limit)')
        parser.add_argument('--overwrite', action='store_true', help='Re-fetch even if poster already exists')

    def handle(self, *args, **options):
        api_key = options['api_key']
        limit = options['limit']
        overwrite = options['overwrite']

        os.makedirs(POSTERS_DIR, exist_ok=True)

        # Load links.csv to build movielens_id -> imdb_id map
        links_path = os.path.join(settings.BASE_DIR, 'datasets', 'ml-latest-small', 'links.csv')
        if not os.path.exists(links_path):
            self.stderr.write(self.style.ERROR(f'links.csv not found at {links_path}'))
            return

        import pandas as pd
        links_df = pd.read_csv(links_path)
        links_df['imdbId'] = links_df['imdbId'].astype(str).str.zfill(7)
        id_map = dict(zip(links_df['movieId'], links_df['imdbId']))

        # Get movies missing posters
        movies = Movie.objects.all()
        if not overwrite:
            movies = movies.filter(poster='')

        total_available = movies.count()
        movies = movies[:limit]

        self.stdout.write(f'Movies missing posters: {total_available}')
        self.stdout.write(f'Processing up to {limit} today (OMDB free tier limit)...\n')

        found = 0
        not_found = 0
        errors = 0

        for i, movie in enumerate(movies, 1):
            imdb_id = id_map.get(movie.movielens_id)
            if not imdb_id:
                not_found += 1
                continue

            try:
                resp = requests.get(OMDB_URL, params={
                    'apikey': api_key,
                    'i': f'tt{imdb_id}',
                    'r': 'json',
                }, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                poster_url = data.get('Poster', '')
                if not poster_url or poster_url == 'N/A':
                    not_found += 1
                    if i % 100 == 0:
                        self.stdout.write(f'  {i} processed — {found} downloaded, {not_found} not found')
                    time.sleep(0.1)
                    continue

                # Download the image
                img_resp = requests.get(poster_url, timeout=15)
                img_resp.raise_for_status()

                filename = f'{movie.pk}_{safe_filename(movie.title)}.jpg'
                filepath = os.path.join(POSTERS_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_resp.content)

                # Update movie.poster field (relative to MEDIA_ROOT)
                movie.poster = f'movies/posters/{filename}'
                Movie.objects.filter(pk=movie.pk).update(poster=f'movies/posters/{filename}')
                found += 1

                if i % 100 == 0:
                    self.stdout.write(f'  {i} processed — {found} downloaded, {not_found} not found')

                time.sleep(0.15)

            except requests.exceptions.RequestException as e:
                errors += 1
                if errors <= 5:
                    self.stderr.write(f'  Error on "{movie.title}": {e}')
                time.sleep(1)

        remaining = total_available - found - not_found - errors
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Downloaded: {found}, Not found: {not_found}, Errors: {errors}'
        ))
        if remaining > 0:
            self.stdout.write(f'Remaining (run again tomorrow): ~{total_available - found}')
