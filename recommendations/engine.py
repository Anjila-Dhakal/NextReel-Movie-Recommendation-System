import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings


_svd_cache = {'data': None, 'mtime': None}


def load_svd_model():
    
    model_path = settings.SVD_MODEL_PATH
    if not os.path.exists(model_path):
        return None
    mtime = os.path.getmtime(model_path)
    if _svd_cache['data'] is None or mtime != _svd_cache['mtime']:
        with open(model_path, 'rb') as f:
            _svd_cache['data'] = pickle.load(f)
        _svd_cache['mtime'] = mtime
    return _svd_cache['data']


GENRE_WEIGHT = 1.0      
MIN_VOTES = 10          


def _genre_profile(user_id):
    
    from reviews.models import Review

    profile = {}
    reviews = Review.objects.filter(user_id=user_id).prefetch_related('movie__genres')
    for review in reviews:
        weight = review.rating - 3
        for genre in review.movie.genres.all():
            profile[genre.id] = profile.get(genre.id, 0) + weight

    max_abs = max((abs(v) for v in profile.values()), default=0)
    if max_abs:
        profile = {g: v / max_abs for g, v in profile.items()}
    return profile


def _genre_affinity(movie, profile):
    genre_ids = [g.id for g in movie.genres.all()]
    if not genre_ids or not profile:
        return 0.0
    return sum(profile.get(g, 0.0) for g in genre_ids) / len(genre_ids)


def _genre_based_picks(profile, exclude_ids, n):
    
    from django.db.models import Avg, ExpressionWrapper, F, FloatField
    from movies.models import Movie

    liked = [g for g, v in sorted(profile.items(), key=lambda x: x[1], reverse=True) if v > 0][:3]

    qs = Movie.objects.exclude(id__in=exclude_ids)
    if liked:
        qs = qs.filter(genres__id__in=liked).distinct()

    mean = Movie.objects.filter(total_ratings__gt=0).aggregate(m=Avg('avg_rating'))['m'] or 3.0
    weighted = ExpressionWrapper(
        (F('avg_rating') * F('total_ratings') + mean * MIN_VOTES) / (F('total_ratings') + MIN_VOTES),
        output_field=FloatField(),
    )
    qs = qs.annotate(weighted=weighted).order_by('-weighted', '-total_watches')
    return list(qs.prefetch_related('genres')[:n])


def _popular_fallback(n):
    from movies.models import Movie
    return list(Movie.objects.order_by('-avg_rating').prefetch_related('genres')[:n])


def get_recommendations(user_id, n=20):
    
    from movies.models import Movie
    from reviews.models import Review

    try:
        rated_movie_ids = set(
            Review.objects.filter(user_id=user_id).values_list('movie_id', flat=True)
        )
        profile = _genre_profile(user_id)

        model_data = load_svd_model()
        str_user_id = str(user_id)
        if model_data is None or str_user_id not in model_data['user_index']:
            return _genre_based_picks(profile, rated_movie_ids, n) or _popular_fallback(n)

        user_factors = model_data['user_factors']
        item_factors = model_data['item_factors']
        item_index = model_data['item_index']
        global_mean = model_data['global_mean']
        user_bias = model_data['user_bias']
        item_bias = model_data['item_bias']

        uidx = model_data['user_index'][str_user_id]
        u_vec = user_factors[uidx]
        u_bias = user_bias[uidx]

        # Normalise keys: older models stored ids as '8911.0' instead of '8911'
        ml_to_idx = {int(float(k)): v for k, v in item_index.items()}

        # Only movies the model has learned about get an SVD score
        known_movies = (
            Movie.objects.filter(movielens_id__in=list(ml_to_idx))
            .exclude(id__in=rated_movie_ids)
            .prefetch_related('genres')
        )

        predictions = []
        for movie in known_movies:
            iidx = ml_to_idx[movie.movielens_id]
            pred = global_mean + u_bias + item_bias[iidx] + np.dot(u_vec, item_factors[iidx])
            pred = float(np.clip(pred, 1.0, 5.0))
            score = pred + GENRE_WEIGHT * _genre_affinity(movie, profile)
            predictions.append((movie, score))

        predictions.sort(key=lambda x: x[1], reverse=True)
        results = [movie for movie, _ in predictions[:n]]

        if len(results) < n:
            exclude = rated_movie_ids | {m.id for m in results}
            results += _genre_based_picks(profile, exclude, n - len(results))

        return results or _popular_fallback(n)

    except Exception:
        return _popular_fallback(n)


def get_cold_start_recommendations(n=12):
    
    from movies.models import Movie
    return {
        'trending': list(Movie.objects.order_by('-total_watches').prefetch_related('genres')[:n]),
        'top_rated': list(Movie.objects.order_by('-avg_rating').prefetch_related('genres')[:n]),
        'new_releases': list(Movie.objects.order_by('-year', '-avg_rating').prefetch_related('genres')[:n]),
    }


def train_svd_model():
    
    from reviews.models import Review

    print('Loading ratings from database...', flush=True)

    reviews_qs = Review.objects.all().values(
        'user_id',
        'movie__movielens_id',
        'rating'
    )

    if not reviews_qs.exists():
        print(
            'No reviews in database. Please add some ratings first.',
            flush=True
        )
        return None

    df = pd.DataFrame(list(reviews_qs))

    df.columns = ['user_id', 'item_id', 'rating']

    # Remove invalid data
    df = df.dropna(subset=['user_id', 'item_id', 'rating'])

    if df.empty:
        print('No valid ratings found.', flush=True)
        return None

    # Cast through int: NaN rows make pandas store ids as floats ('8911.0')
    df['user_id'] = df['user_id'].astype(int).astype(str)
    df['item_id'] = df['item_id'].astype(int).astype(str)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

    df = df.dropna(subset=['rating'])

    if df.empty:
        print('No valid numeric ratings found.', flush=True)
        return None

    n_users = df['user_id'].nunique()
    n_items = df['item_id'].nunique()

    print(
        f'Training SVD on {len(df)} ratings, '
        f'{n_users} users, {n_items} movies...',
        flush=True
    )

    # Build index maps
    user_index = {
        user_id: index
        for index, user_id in enumerate(df['user_id'].unique())
    }

    item_index = {
        item_id: index
        for index, item_id in enumerate(df['item_id'].unique())
    }

    # Hyperparameters
    n_factors = 50
    n_epochs = 30
    lr = 0.005
    reg = 0.02

    global_mean = float(df['rating'].mean())

    # Initialize factors
    rng = np.random.RandomState(42)

    user_factors = rng.normal(
        0,
        0.1,
        (len(user_index), n_factors)
    )

    item_factors = rng.normal(
        0,
        0.1,
        (len(item_index), n_factors)
    )

    user_bias = np.zeros(len(user_index))
    item_bias = np.zeros(len(item_index))

    # Convert ratings to integer indexes BEFORE training
    training_rows = []

    for _, row in df.iterrows():

        uid = str(row['user_id'])
        iid = str(row['item_id'])
        rating = float(row['rating'])

        training_rows.append(
            (
                user_index[uid],
                item_index[iid],
                rating
            )
        )

    print(
        f'Starting SVD training for {n_epochs} epochs...',
        flush=True
    )

    

    for epoch in range(n_epochs):

        np.random.shuffle(training_rows)

        total_loss = 0.0

        for u, i, rating in training_rows:

            # Prediction
            prediction = (
                global_mean
                + user_bias[u]
                + item_bias[i]
                + np.dot(
                    user_factors[u],
                    item_factors[i]
                )
            )

            # Error
            error = rating - prediction

            total_loss += error ** 2

            # Save old user factors
            old_user_factors = user_factors[u].copy()

            # Update biases
            user_bias[u] += lr * (
                error - reg * user_bias[u]
            )

            item_bias[i] += lr * (
                error - reg * item_bias[i]
            )

            # Update latent factors
            user_factors[u] += lr * (
                error * item_factors[i]
                - reg * user_factors[u]
            )

            item_factors[i] += lr * (
                error * old_user_factors
                - reg * item_factors[i]
            )

        rmse = np.sqrt(
            total_loss / len(training_rows)
        )

        # Print every epoch for debugging
        print(
            f'Epoch {epoch + 1}/{n_epochs} '
            f'— RMSE: {rmse:.4f}',
            flush=True
        )

    

    model_data = {
        'user_factors': user_factors,
        'item_factors': item_factors,
        'user_index': user_index,
        'item_index': item_index,
        'global_mean': global_mean,
        'user_bias': user_bias,
        'item_bias': item_bias,
        'n_factors': n_factors,
    }

    model_dir = Path(
        settings.SVD_MODEL_PATH
    ).parent

    model_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        settings.SVD_MODEL_PATH,
        'wb'
    ) as f:
        pickle.dump(model_data, f)

    # Clear cache
    _svd_cache['data'] = None
    _svd_cache['mtime'] = None

    print(
        f'SVD model saved to {settings.SVD_MODEL_PATH}',
        flush=True
    )

    return model_data