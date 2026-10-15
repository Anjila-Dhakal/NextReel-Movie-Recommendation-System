"""
Usage: python manage.py import_nepali_movies --api-key YOUR_OMDB_KEY

Imports popular Nepali movies into the database.
Fetches poster and metadata from OMDB using IMDB IDs or title search.
Uses movielens_id starting from 99001 to avoid conflicts.
"""
import time

import requests
from django.core.management.base import BaseCommand

from movies.models import Genre, Movie

OMDB_URL = 'http://www.omdbapi.com/'

# Popular Nepali movies with IMDB IDs for accurate matching
NEPALI_MOVIES = [
    {'title': 'Loot', 'year': 2012, 'imdb_id': 'tt2386140'},
    {'title': 'Kabaddi', 'year': 2014, 'imdb_id': 'tt3863552'},
    {'title': 'Pashupati Prasad', 'year': 2016, 'imdb_id': 'tt5545428'},
    {'title': 'Loot 2', 'year': 2017, 'imdb_id': 'tt6857988'},
    {'title': 'Kabaddi Kabaddi', 'year': 2015, 'imdb_id': 'tt4687922'},
    {'title': 'Chhakka Panja', 'year': 2016, 'imdb_id': 'tt6042050'},
    {'title': 'Chhakka Panja 2', 'year': 2017, 'imdb_id': 'tt7528794'},
    {'title': 'Chhakka Panja 3', 'year': 2018, 'imdb_id': 'tt8664992'},
    {'title': 'Bir Bikram', 'year': 2016, 'imdb_id': 'tt5874518'},
    {'title': 'Bir Bikram 2', 'year': 2018, 'imdb_id': 'tt8385390'},
    {'title': 'Sungava Bhauju', 'year': 2015, 'imdb_id': 'tt4687876'},
    {'title': 'Hostel', 'year': 2013, 'imdb_id': 'tt2953062'},
    {'title': 'Hostel Returns', 'year': 2018, 'imdb_id': 'tt8398028'},
    {'title': 'Jerry', 'year': 2018, 'imdb_id': 'tt7846844'},
    {'title': 'Dream Girl', 'year': 2018, 'imdb_id': 'tt8221958'},
    {'title': 'Woda Number 6', 'year': 2014, 'imdb_id': 'tt3863526'},
    {'title': 'Resham Filili', 'year': 2017, 'imdb_id': 'tt6857944'},
    {'title': 'Jatra', 'year': 2016, 'imdb_id': 'tt5853540'},
    {'title': 'Kohi Mero', 'year': 2016, 'imdb_id': None},
    {'title': 'Talakjung vs Tulke', 'year': 2014, 'imdb_id': 'tt3863538'},
    {'title': 'Nai Nabhannu La', 'year': 2011, 'imdb_id': 'tt2100949'},
    {'title': 'Nai Nabhannu La 2', 'year': 2012, 'imdb_id': 'tt2386124'},
    {'title': 'Nai Nabhannu La 3', 'year': 2013, 'imdb_id': 'tt2953048'},
    {'title': 'Nai Nabhannu La 4', 'year': 2014, 'imdb_id': 'tt3863514'},
    {'title': 'Nai Nabhannu La 5', 'year': 2015, 'imdb_id': 'tt4687864'},
    {'title': 'Darpan Chhaya', 'year': 2001, 'imdb_id': 'tt0290351'},
    {'title': 'Kagbeni', 'year': 2008, 'imdb_id': 'tt1334555'},
    {'title': 'Numafung', 'year': 2004, 'imdb_id': 'tt0388640'},
    {'title': 'Mero Euta Saathi Chha', 'year': 2016, 'imdb_id': 'tt5853528'},
    {'title': 'Badhshala', 'year': 2015, 'imdb_id': 'tt4687852'},
    {'title': 'Purano Dunga', 'year': 2019, 'imdb_id': 'tt9686170'},
    {'title': 'Sufi', 'year': 2018, 'imdb_id': 'tt8664968'},
    {'title': 'Seto Surya', 'year': 2016, 'imdb_id': 'tt5853516'},
    {'title': 'Prem Geet', 'year': 2016, 'imdb_id': 'tt5853504'},
    {'title': 'Prem Geet 2', 'year': 2018, 'imdb_id': 'tt8398016'},
    {'title': 'Prem Geet 3', 'year': 2021, 'imdb_id': 'tt13888712'},
    {'title': 'A Mero Hajur', 'year': 2016, 'imdb_id': 'tt5853492'},
    {'title': 'A Mero Hajur 2', 'year': 2017, 'imdb_id': 'tt7528782'},
    {'title': 'A Mero Hajur 3', 'year': 2018, 'imdb_id': 'tt8664980'},
    {'title': 'Kri', 'year': 2019, 'imdb_id': 'tt9686194'},
    {'title': 'Lalbandi', 'year': 2019, 'imdb_id': 'tt9686182'},
    {'title': 'Masan', 'year': 2014, 'imdb_id': 'tt3863500'},
    {'title': 'Bir Bikram 3', 'year': 2022, 'imdb_id': 'tt18026798'},
    {'title': 'Ninu', 'year': 2019, 'imdb_id': 'tt9686158'},
    {'title': 'Bulbul', 'year': 2019, 'imdb_id': 'tt9686146'},
    {'title': 'Swasni Manchhe Ko Laure', 'year': 2019, 'imdb_id': 'tt9686134'},
    {'title': 'Guru', 'year': 2019, 'imdb_id': 'tt9686122'},
    {'title': 'Mandala', 'year': 2020, 'imdb_id': 'tt11564226'},
    {'title': 'Shree 3', 'year': 2022, 'imdb_id': 'tt18026786'},
    {'title': 'Fighters', 'year': 2022, 'imdb_id': 'tt18026774'},
]


class Command(BaseCommand):
    help = 'Import popular Nepali movies with metadata and posters from OMDB'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, required=True, help='OMDB API key')

    def handle(self, *args, **options):
        api_key = options['api_key']

        # Ensure Nepali genre exists
        nepali_genre, _ = Genre.objects.get_or_create(name='Nepali')

        # Find next available movielens_id starting from 999001 (safely above MovieLens max of 193609)
        start_id = 999001
        existing_ids = set(Movie.objects.filter(movielens_id__gte=999001).values_list('movielens_id', flat=True))
        next_id = start_id
        while next_id in existing_ids:
            next_id += 1

        imported = 0
        updated = 0
        no_data = 0

        for movie_data in NEPALI_MOVIES:
            title = movie_data['title']
            year = movie_data['year']
            imdb_id = movie_data['imdb_id']

            # Check if already exists
            existing = Movie.objects.filter(title=title, year=year).first()

            # Fetch from OMDB
            omdb_data = {}
            poster_url = None
            try:
                if imdb_id:
                    params = {'apikey': api_key, 'i': imdb_id, 'r': 'json'}
                else:
                    params = {'apikey': api_key, 't': title, 'y': year, 'r': 'json'}

                resp = requests.get(OMDB_URL, params=params, timeout=10)
                resp.raise_for_status()
                omdb_data = resp.json()

                if omdb_data.get('Response') == 'True':
                    poster_url = omdb_data.get('Poster', '')
                    if poster_url == 'N/A':
                        poster_url = None
                time.sleep(0.2)
            except Exception as e:
                self.stderr.write(f'  OMDB error for "{title}": {e}')

            # Build description from OMDB plot
            description = omdb_data.get('Plot', '')
            if description == 'N/A':
                description = ''

            # Get or infer genres from OMDB
            genre_names = ['Nepali']
            omdb_genres = omdb_data.get('Genre', '')
            if omdb_genres and omdb_genres != 'N/A':
                for g in omdb_genres.split(','):
                    g = g.strip()
                    if g and g not in genre_names:
                        genre_names.append(g)

            if existing:
                # Update description and genres if missing
                if not existing.description and description:
                    existing.description = description
                    existing.save(update_fields=['description'])
                updated += 1
                movie_obj = existing
            else:
                movie_obj = Movie.objects.create(
                    title=title,
                    year=year,
                    movielens_id=next_id,
                    description=description,
                    avg_rating=0.0,
                    total_ratings=0,
                    total_watches=0,
                )
                next_id += 1
                while next_id in existing_ids:
                    next_id += 1
                existing_ids.add(movie_obj.movielens_id)
                imported += 1

            # Assign genres
            genre_objs = []
            for gname in genre_names:
                g_obj, _ = Genre.objects.get_or_create(name=gname)
                genre_objs.append(g_obj)
            movie_obj.genres.set(genre_objs)

            # Download and save poster
            if poster_url and not movie_obj.poster:
                try:
                    import os, re
                    from django.conf import settings
                    img_resp = requests.get(poster_url, timeout=15)
                    img_resp.raise_for_status()
                    posters_dir = os.path.join(settings.MEDIA_ROOT, 'movies', 'posters')
                    os.makedirs(posters_dir, exist_ok=True)
                    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
                    safe_title = re.sub(r'\s+', '_', safe_title)[:40]
                    filename = f'{movie_obj.pk}_{safe_title}.jpg'
                    filepath = os.path.join(posters_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(img_resp.content)
                    movie_obj.poster = f'movies/posters/{filename}'
                    movie_obj.save(update_fields=['poster'])
                except Exception as e:
                    self.stderr.write(f'  Poster download error for "{title}": {e}')

            self.stdout.write(f'  {"Added" if not existing else "Updated"}: {title} ({year})')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Imported: {imported}, Updated: {updated}, No OMDB data: {no_data}'
        ))
        self.stdout.write(f'Total Nepali movies in DB: {Movie.objects.filter(genres__name="Nepali").count()}')
