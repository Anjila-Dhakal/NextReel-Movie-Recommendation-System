"""
Usage: python manage.py train_svd
Trains the SVD collaborative filtering model using all Review data in the database.
The model is saved to the path specified by SVD_MODEL_PATH in settings.py.

Prerequisites:
- Run `python manage.py import_movies` first to populate the movies database.
- Users must have submitted ratings (reviews) for the model to train on.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train SVD collaborative filtering model from review data in the database'

    def handle(self, *args, **options):
        self.stdout.write('Starting SVD model training...')
        self.stdout.write('This may take a few minutes depending on the size of your dataset.')

        from recommendations.engine import train_svd_model
        algo = train_svd_model()

        if algo is not None:
            self.stdout.write(self.style.SUCCESS('SVD model training complete!'))
        else:
            self.stdout.write(self.style.ERROR(
                'SVD training failed. Ensure reviews exist in the database '
                'and scikit-surprise is installed.'
            ))
