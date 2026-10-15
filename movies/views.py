from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView

from .forms import SearchForm
from reviews.forms import ReviewForm
from .models import Genre, Movie, Watchlist, WatchHistory


class HomeView(View):
    template_name = 'movies/home.html'

    def get(self, request):
        context = {
            'featured_movies': Movie.objects.order_by('-avg_rating')[:8],
            'trending_movies': Movie.objects.order_by('-total_watches')[:8],
            'new_releases': Movie.objects.order_by('-year', '-avg_rating')[:8],
            'latest_movies': Movie.objects.filter(
                year__gte=2020, tmdb_id__isnull=False
            ).order_by('-year', '-avg_rating')[:12],
            'genres': Genre.objects.all().order_by('name'),
        }
        return render(request, self.template_name, context)


class MovieListView(View):
    template_name = 'movies/list.html'
    paginate_by = 20

    def get(self, request):
        movies = Movie.objects.all().prefetch_related('genres')
        form = SearchForm(request.GET)

        # Apply filters
        genre_id = request.GET.get('genre_id') or request.GET.get('genre')
        q = request.GET.get('q', '').strip()
        year_from = request.GET.get('year_from')
        year_to = request.GET.get('year_to')
        min_rating = request.GET.get('min_rating')

        if q:
            title_q = Q()
            for word in q.split():
                title_q &= Q(title__icontains=word)
            movies = movies.filter(title_q)

        if genre_id:
            try:
                movies = movies.filter(genres__id=int(genre_id))
            except (ValueError, TypeError):
                pass

        if year_from:
            try:
                movies = movies.filter(year__gte=int(year_from))
            except (ValueError, TypeError):
                pass

        if year_to:
            try:
                movies = movies.filter(year__lte=int(year_to))
            except (ValueError, TypeError):
                pass

        if min_rating:
            try:
                movies = movies.filter(avg_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass

        movies = movies.distinct()

        paginator = Paginator(movies, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        selected_genre = None
        if genre_id:
            try:
                selected_genre = Genre.objects.get(id=int(genre_id))
            except (Genre.DoesNotExist, ValueError, TypeError):
                pass

        watchlisted_ids = set()
        if request.user.is_authenticated:
            watchlisted_ids = set(
                Watchlist.objects.filter(
                    user=request.user,
                    movie_id__in=[m.pk for m in page_obj.object_list],
                ).values_list('movie_id', flat=True)
            )

        context = {
            'page_obj': page_obj,
            'movies': page_obj,
            'genres': Genre.objects.all().order_by('name'),
            'selected_genre': selected_genre,
            'search_query': q,
            'year_from': year_from or '',
            'year_to': year_to or '',
            'min_rating': min_rating or '',
            'watchlisted_ids': watchlisted_ids,
            'total_count': paginator.count,
        }
        return render(request, self.template_name, context)


class MovieDetailView(View):
    template_name = 'movies/detail.html'

    def get(self, request, pk):
        movie = get_object_or_404(Movie.objects.prefetch_related('genres', 'reviews__user'), pk=pk)

        from reviews.models import Review

        user_review = None
        in_watchlist = False
        already_watched = False

        if request.user.is_authenticated:
            user_review = Review.objects.filter(user=request.user, movie=movie).first()
            in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()
            already_watched = WatchHistory.objects.filter(user=request.user, movie=movie).exists()

        reviews = movie.reviews.select_related('user').order_by('-created_at')[:10]
        related_movies = Movie.objects.filter(
            genres__in=movie.genres.all()
        ).exclude(pk=movie.pk).distinct()[:6]

        context = {
            'movie': movie,
            'reviews': reviews,
            'user_review': user_review,
            'in_watchlist': in_watchlist,
            'already_watched': already_watched,
            'related_movies': related_movies,
            'genre_list': movie.genres.all(),
            'form': ReviewForm(),
        }
        return render(request, self.template_name, context)


class SearchView(View):
    template_name = 'movies/search.html'
    paginate_by = 20

    def get(self, request):
        form = SearchForm(request.GET)

        q = request.GET.get('q', '').strip()
        genre_id = request.GET.get('genre_id') or request.GET.get('genre')
        year_from = request.GET.get('year_from', '').strip()
        year_to = request.GET.get('year_to', '').strip()
        min_rating = request.GET.get('min_rating', '').strip()

        movies = Movie.objects.all().prefetch_related('genres')

        if q:
            title_q = Q()
            for word in q.split():
                title_q &= Q(title__icontains=word)
            movies = movies.filter(title_q)

        if genre_id:
            try:
                movies = movies.filter(genres__id=int(genre_id))
            except (ValueError, TypeError):
                pass

        if year_from:
            try:
                movies = movies.filter(year__gte=int(year_from))
            except (ValueError, TypeError):
                pass

        if year_to:
            try:
                movies = movies.filter(year__lte=int(year_to))
            except (ValueError, TypeError):
                pass

        if min_rating:
            try:
                movies = movies.filter(avg_rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass

        movies = movies.distinct()

        paginator = Paginator(movies, self.paginate_by)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        selected_genre_name = None
        if genre_id:
            try:
                selected_genre = Genre.objects.get(pk=int(genre_id))
                selected_genre_name = selected_genre.name
            except (Genre.DoesNotExist, ValueError, TypeError):
                selected_genre = None
                selected_genre_name = None
        else:
            selected_genre = None

        context = {
            'page_obj': page_obj,
            'movies': page_obj,
            'genres': Genre.objects.all().order_by('name'),
            'form': form,
            'search_query': q,
            'selected_genre': selected_genre,
            'selected_genre_name': selected_genre_name,
            'year_from': year_from,
            'year_to': year_to,
            'min_rating': min_rating,
            'total_count': paginator.count,
        }
        return render(request, self.template_name, context)


class AddToWatchlistView(LoginRequiredMixin, View):
    login_url = '/users/login/'

    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        watchlist_item, created = Watchlist.objects.get_or_create(
            user=request.user,
            movie=movie,
        )
        if not created:
            watchlist_item.delete()
            in_watchlist = False
            message = f'"{movie.title}" removed from your watchlist.'
        else:
            in_watchlist = True
            message = f'"{movie.title}" added to your watchlist.'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'in_watchlist': in_watchlist, 'message': message})

        messages.success(request, message)
        next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
        if next_url:
            return redirect(next_url)
        return redirect('movies:detail', pk=pk)


class RecordWatchView(LoginRequiredMixin, View):
    login_url = '/users/login/'

    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)

        _, created = WatchHistory.objects.get_or_create(user=request.user, movie=movie)
        if created:
            Movie.objects.filter(pk=pk).update(total_watches=F('total_watches') + 1)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'message': f'Marked "{movie.title}" as watched.'})

        messages.success(request, f'"{movie.title}" marked as watched.')
        return redirect('movies:detail', pk=pk)
