"""
Demo seed command — populates 30 iconic movies, sample users, ratings, and reviews.
Usage: python manage.py seed_demo
"""
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from movies.models import Genre, Movie, Watchlist, WatchHistory
from reviews.models import Review

User = get_user_model()

GENRES_LIST = [
    'Action', 'Adventure', 'Animation', 'Comedy', 'Crime',
    'Documentary', 'Drama', 'Fantasy', 'Horror', 'Mystery',
    'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western',
]

MOVIES_DATA = [
    {'id': 1, 'title': 'The Shawshank Redemption', 'year': 1994, 'genres': ['Drama'], 'avg': 4.9,
     'desc': 'Two imprisoned men bond over years, finding solace and eventual redemption through acts of decency.'},
    {'id': 2, 'title': 'The Godfather', 'year': 1972, 'genres': ['Crime', 'Drama'], 'avg': 4.8,
     'desc': 'The aging patriarch of an organized crime dynasty transfers control to his reluctant son.'},
    {'id': 3, 'title': 'The Dark Knight', 'year': 2008, 'genres': ['Action', 'Crime', 'Drama'], 'avg': 4.8,
     'desc': 'Batman faces his greatest challenge yet when a criminal mastermind known as the Joker wreaks havoc.'},
    {'id': 4, 'title': 'Schindler\'s List', 'year': 1993, 'genres': ['Drama', 'War'], 'avg': 4.8,
     'desc': "German businessman Oskar Schindler saves over a thousand Jewish lives during the Holocaust."},
    {'id': 5, 'title': 'Pulp Fiction', 'year': 1994, 'genres': ['Crime', 'Drama'], 'avg': 4.7,
     'desc': 'The lives of two mob hitmen, a boxer, and a pair of diner bandits intertwine in four tales of violence.'},
    {'id': 6, 'title': 'The Lord of the Rings: The Return of the King', 'year': 2003, 'genres': ['Action', 'Adventure', 'Drama', 'Fantasy'], 'avg': 4.8,
     'desc': "Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze from Frodo."},
    {'id': 7, 'title': 'The Good, the Bad and the Ugly', 'year': 1966, 'genres': ['Adventure', 'Western'], 'avg': 4.7,
     'desc': 'A bounty hunting scam joins two men in an uneasy alliance against a third in a race to find buried gold.'},
    {'id': 8, 'title': 'Inception', 'year': 2010, 'genres': ['Action', 'Adventure', 'Sci-Fi', 'Thriller'], 'avg': 4.7,
     'desc': 'A thief who steals corporate secrets through dreams is given a chance to erase his past.'},
    {'id': 9, 'title': 'The Matrix', 'year': 1999, 'genres': ['Action', 'Sci-Fi'], 'avg': 4.6,
     'desc': 'A computer hacker learns that reality as we know it is a simulation and joins a rebellion.'},
    {'id': 10, 'title': 'Goodfellas', 'year': 1990, 'genres': ['Biography', 'Crime', 'Drama'], 'avg': 4.7,
     'desc': "Henry Hill and his friends rise through the mob ranks and then fall as government witnesses."},
    {'id': 11, 'title': 'One Flew Over the Cuckoo\'s Nest', 'year': 1975, 'genres': ['Drama'], 'avg': 4.7,
     'desc': "A criminal pleads insanity and is admitted to a mental institution, where he fights the system."},
    {'id': 12, 'title': 'Interstellar', 'year': 2014, 'genres': ['Adventure', 'Drama', 'Sci-Fi'], 'avg': 4.6,
     'desc': "A team of explorers travel through a wormhole in space to ensure humanity's survival."},
    {'id': 13, 'title': 'Parasite', 'year': 2019, 'genres': ['Comedy', 'Drama', 'Thriller'], 'avg': 4.6,
     'desc': 'Greed and class discrimination threaten the newly formed symbiotic relationship between two families.'},
    {'id': 14, 'title': 'Spirited Away', 'year': 2001, 'genres': ['Animation', 'Adventure', 'Fantasy'], 'avg': 4.6,
     'desc': "A sullen girl wanders into a world ruled by gods, witches, and spirits where humans are turned into animals."},
    {'id': 15, 'title': 'The Silence of the Lambs', 'year': 1991, 'genres': ['Crime', 'Drama', 'Thriller'], 'avg': 4.6,
     'desc': "A young FBI cadet must receive the help of an incarcerated and manipulative cannibal killer."},
    {'id': 16, 'title': 'Avengers: Endgame', 'year': 2019, 'genres': ['Action', 'Adventure', 'Drama', 'Sci-Fi'], 'avg': 4.4,
     'desc': 'After the devastating events of Infinity War, the Avengers assemble once more to reverse Thanos\'s actions.'},
    {'id': 17, 'title': 'The Grand Budapest Hotel', 'year': 2014, 'genres': ['Adventure', 'Comedy', 'Crime', 'Drama'], 'avg': 4.3,
     'desc': "The adventures of a legendary concierge and his lobby boy protégé across a fictional European hotel."},
    {'id': 18, 'title': 'Forrest Gump', 'year': 1994, 'genres': ['Drama', 'Romance'], 'avg': 4.5,
     'desc': 'The presidencies of Kennedy and Johnson, Vietnam, Watergate, and other events unfold through a slow-witted man.'},
    {'id': 19, 'title': 'City of God', 'year': 2002, 'genres': ['Crime', 'Drama'], 'avg': 4.6,
     'desc': 'Two boys growing up in a violent neighborhood in Rio de Janeiro take different paths.'},
    {'id': 20, 'title': 'Whiplash', 'year': 2014, 'genres': ['Drama', 'Music'], 'avg': 4.5,
     'desc': "A young drummer enrolls at a cutthroat music conservatory where his instructor's terrifying demands push him."},
    {'id': 21, 'title': 'The Lion King', 'year': 1994, 'genres': ['Animation', 'Adventure', 'Drama', 'Fantasy'], 'avg': 4.4,
     'desc': 'Lion cub Simba idolizes his father, King Mufasa, and takes to heart his lessons in life.'},
    {'id': 22, 'title': 'Back to the Future', 'year': 1985, 'genres': ['Adventure', 'Comedy', 'Sci-Fi'], 'avg': 4.5,
     'desc': 'A teenager is accidentally sent 30 years into the past in a time-traveling DeLorean.'},
    {'id': 23, 'title': 'Gladiator', 'year': 2000, 'genres': ['Action', 'Adventure', 'Drama'], 'avg': 4.4,
     'desc': 'A Roman general becomes a slave and fights as a gladiator to avenge his murdered family.'},
    {'id': 24, 'title': 'The Prestige', 'year': 2006, 'genres': ['Drama', 'Mystery', 'Sci-Fi', 'Thriller'], 'avg': 4.5,
     'desc': 'Two stage magicians engage in a competitive rivalry that culminates in murderous obsession.'},
    {'id': 25, 'title': 'WALL-E', 'year': 2008, 'genres': ['Animation', 'Adventure', 'Comedy', 'Romance', 'Sci-Fi'], 'avg': 4.3,
     'desc': 'A small waste-collecting robot inadvertently embarks on a space journey that will ultimately decide the fate of mankind.'},
    {'id': 26, 'title': 'The Departed', 'year': 2006, 'genres': ['Crime', 'Drama', 'Thriller'], 'avg': 4.6,
     'desc': 'An undercover cop and a mole in the police attempt to identify each other while simultaneously police try to identify the mole.'},
    {'id': 27, 'title': 'No Country for Old Men', 'year': 2007, 'genres': ['Crime', 'Drama', 'Thriller'], 'avg': 4.4,
     'desc': 'Violence and mayhem ensue after a hunter stumbles upon a drug deal gone wrong.'},
    {'id': 28, 'title': 'Toy Story', 'year': 1995, 'genres': ['Animation', 'Adventure', 'Comedy', 'Fantasy'], 'avg': 4.3,
     'desc': "A cowboy doll is profoundly threatened when a new spaceman figure becomes his owner's favorite toy."},
    {'id': 29, 'title': 'Amélie', 'year': 2001, 'genres': ['Comedy', 'Romance'], 'avg': 4.4,
     'desc': 'At age 23, Amélie discovers a gift for positively influencing the lives of others through her imagination.'},
    {'id': 30, 'title': 'Oldboy', 'year': 2003, 'genres': ['Action', 'Drama', 'Mystery', 'Thriller'], 'avg': 4.5,
     'desc': "After being imprisoned for 15 years without explanation, a man is released and given five days to find his captor."},
]

SAMPLE_REVIEWS = [
    ("Absolutely masterpiece. The storytelling is unparalleled and the performances are extraordinary.", "positive"),
    ("One of the greatest films ever made. A must-watch for every cinema lover.", "positive"),
    ("Brilliant direction and incredible acting. Left me speechless.", "positive"),
    ("A timeless classic. The cinematography is stunning and the plot is gripping.", "positive"),
    ("Exceeded all expectations. The ending was perfect and emotional.", "positive"),
    ("Disappointing. The pacing was slow and the story felt incomplete.", "negative"),
    ("Not my type of film. Too long and the characters were underdeveloped.", "negative"),
    ("Overrated in my opinion. The hype didn't match the experience.", "negative"),
    ("Good film with some great moments, though not without its flaws.", "positive"),
    ("A visual spectacle with deep themes. Highly recommended.", "positive"),
    ("The soundtrack is phenomenal and perfectly complements the visuals.", "positive"),
    ("Groundbreaking filmmaking that changed the industry forever.", "positive"),
    ("Extremely suspenseful from start to finish. Could not look away.", "positive"),
    ("The character development is superb. You genuinely care about everyone.", "positive"),
    ("A dark and disturbing watch, but incredibly well crafted.", "positive"),
]

SAMPLE_USERS = [
    {'username': 'cinephile_raj', 'email': 'raj@example.com', 'first': 'Raj', 'last': 'Sharma'},
    {'username': 'movie_lover_priya', 'email': 'priya@example.com', 'first': 'Priya', 'last': 'Patel'},
    {'username': 'filmfan_arjun', 'email': 'arjun@example.com', 'first': 'Arjun', 'last': 'Singh'},
    {'username': 'screenwriter_sam', 'email': 'sam@example.com', 'first': 'Sam', 'last': 'Kumar'},
    {'username': 'critic_neha', 'email': 'neha@example.com', 'first': 'Neha', 'last': 'Gupta'},
]


class Command(BaseCommand):
    help = 'Seed database with demo movies, users, and reviews'

    def handle(self, *args, **options):
        self.stdout.write('Creating genres...')
        genre_map = {}
        for g in GENRES_LIST + ['Biography', 'Music']:
            obj, _ = Genre.objects.get_or_create(name=g)
            genre_map[g] = obj

        self.stdout.write('Creating movies...')
        movies = []
        for data in MOVIES_DATA:
            movie, created = Movie.objects.update_or_create(
                movielens_id=data['id'],
                defaults={
                    'title': data['title'],
                    'year': data['year'],
                    'avg_rating': data['avg'],
                    'total_ratings': random.randint(500, 5000),
                    'total_watches': random.randint(1000, 20000),
                    'description': data['desc'],
                }
            )
            movie.genres.set([genre_map[g] for g in data['genres'] if g in genre_map])
            movies.append(movie)
            if created:
                self.stdout.write(f'  + {movie.title}')

        self.stdout.write('Creating demo users...')
        users = []
        for ud in SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                username=ud['username'],
                defaults={
                    'email': ud['email'],
                    'first_name': ud['first'],
                    'last_name': ud['last'],
                    'is_new_user': False,
                }
            )
            if created:
                user.set_password('demo1234')
                user.save()
                self.stdout.write(f'  + User: {user.username}')
            users.append(user)

        self.stdout.write('Creating reviews and ratings...')
        rng = random.Random(99)
        review_count = 0
        for user in users:
            sampled_movies = rng.sample(movies, min(15, len(movies)))
            for movie in sampled_movies:
                if Review.objects.filter(user=user, movie=movie).exists():
                    continue
                text, sentiment = rng.choice(SAMPLE_REVIEWS)
                rating = rng.choice([4, 5]) if sentiment == 'positive' else rng.choice([1, 2, 3])
                Review.objects.create(
                    user=user, movie=movie,
                    rating=rating, review_text=text, sentiment=sentiment,
                )
                review_count += 1

        self.stdout.write('Adding watchlist and watch history...')
        for user in users:
            wl_movies = rng.sample(movies, min(8, len(movies)))
            for movie in wl_movies:
                Watchlist.objects.get_or_create(user=user, movie=movie)
            wh_movies = rng.sample(movies, min(10, len(movies)))
            for movie in wh_movies:
                WatchHistory.objects.create(user=user, movie=movie)

        self.stdout.write(self.style.SUCCESS(
            f'\nDemo data ready!\n'
            f'  Movies: {Movie.objects.count()}\n'
            f'  Genres: {Genre.objects.count()}\n'
            f'  Users:  {User.objects.count()} (admin + {len(users)} demo)\n'
            f'  Reviews:{Review.objects.count()}\n\n'
            f'Login: admin / admin123\n'
            f'Demo users password: demo1234\n'
        ))
