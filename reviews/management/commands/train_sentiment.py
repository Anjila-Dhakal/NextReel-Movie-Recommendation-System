"""
Usage: python manage.py train_sentiment
Trains Naive Bayes sentiment classifier on IMDB dataset.
Requires: datasets/imdb_reviews.csv with columns 'review' and 'sentiment'

The IMDB dataset can be downloaded from:
https://www.kaggle.com/datasets/lakshmi25npathi/imdb-dataset-of-50k-movie-reviews
"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train Naive Bayes sentiment model on IMDB dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset',
            type=str,
            default=str(settings.BASE_DIR / 'datasets' / 'imdb_reviews.csv'),
            help='Path to the IMDB reviews CSV file (default: datasets/imdb_reviews.csv)',
        )

    def handle(self, *args, **options):
        dataset_path = options['dataset']
        self.stdout.write(f'Training sentiment model with dataset: {dataset_path}')
        self.stdout.write('This may take a few minutes...')

        from reviews.sentiment import train_sentiment_model
        accuracy = train_sentiment_model(dataset_path)

        if accuracy is not None:
            self.stdout.write(self.style.SUCCESS(
                f'Training complete! Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                'Training failed. Please check the dataset path and format.'
            ))
