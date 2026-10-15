"""
Usage: python manage.py import_movies
Reads datasets/movies.csv and datasets/ratings.csv (MovieLens 100K format).
movies.csv columns: movieId,title,genres (genres pipe-separated like "Action|Comedy")
ratings.csv columns: userId,movieId,rating,timestamp
"""
import re

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Genre, Movie


class Command(BaseCommand):
    help = 'Import movies from MovieLens CSV dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movies',
            type=str,
            default=str(settings.BASE_DIR / 'datasets' / 'movies.csv'),
            help='Path to movies.csv file',
        )
        parser.add_argument(
            '--ratings',
            type=str,
            default=str(settings.BASE_DIR / 'datasets' / 'ratings.csv'),
            help='Path to ratings.csv file',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of movies to import (for testing)',
        )

    def handle(self, *args, **options):
        movies_path = options['movies']
        ratings_path = options['ratings']
        limit = options.get('limit')

        import os
        if not os.path.exists(movies_path):
            self.stderr.write(self.style.ERROR(f'movies.csv not found at {movies_path}'))
            self.stderr.write('Please place the MovieLens dataset CSV files in the datasets/ directory.')
            return

        self.stdout.write(f'Reading movies dataset from {movies_path}...')
        movies_df = pd.read_csv(movies_path)

        if limit:
            movies_df = movies_df.head(limit)
            self.stdout.write(f'Limiting import to {limit} movies.')

        # Handle ratings if available
        rating_stats = None
        if os.path.exists(ratings_path):
            self.stdout.write(f'Reading ratings dataset from {ratings_path}...')
            ratings_df = pd.read_csv(ratings_path)
            rating_stats = ratings_df.groupby('movieId').agg(
                avg_rating=('rating', 'mean'),
                total_ratings=('rating', 'count'),
            ).reset_index()
            rating_stats['avg_rating'] = rating_stats['avg_rating'].round(2)
        else:
            self.stdout.write(self.style.WARNING(
                f'ratings.csv not found at {ratings_path}. Proceeding without ratings data.'
            ))

        self.stdout.write(f'Importing {len(movies_df)} movies...')
        imported_count = 0
        updated_count = 0

        with transaction.atomic():
            for _, row in movies_df.iterrows():
                # Extract year from title like "Toy Story (1995)"
                year = None
                title = str(row['title'])
                year_match = re.search(r'\((\d{4})\)', title)
                if year_match:
                    year = int(year_match.group(1))
                    title = re.sub(r'\s*\(\d{4}\)', '', title).strip()

                # Get rating stats
                avg_rating = 0.0
                total_ratings = 0
                if rating_stats is not None:
                    stats = rating_stats[rating_stats['movieId'] == row['movieId']]
                    if not stats.empty:
                        avg_rating = float(stats.iloc[0]['avg_rating'])
                        total_ratings = int(stats.iloc[0]['total_ratings'])

                movie, created = Movie.objects.update_or_create(
                    movielens_id=int(row['movieId']),
                    defaults={
                        'title': title,
                        'year': year,
                        'avg_rating': avg_rating,
                        'total_ratings': total_ratings,
                    },
                )

                if created:
                    imported_count += 1
                else:
                    updated_count += 1

                # Handle genres
                genres_str = str(row.get('genres', ''))
                if genres_str and genres_str != '(no genres listed)' and genres_str != 'nan':
                    genre_names = genres_str.split('|')
                    genre_objs = []
                    for genre_name in genre_names:
                        genre_name = genre_name.strip()
                        if genre_name and genre_name != '(no genres listed)':
                            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                            genre_objs.append(genre_obj)
                    movie.genres.set(genre_objs)

        self.stdout.write(self.style.SUCCESS(
            f'Import complete! '
            f'Created: {imported_count}, Updated: {updated_count}, '
            f'Total movies in DB: {Movie.objects.count()}'
        ))
