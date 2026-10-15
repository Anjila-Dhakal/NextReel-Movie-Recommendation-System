from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from movies.forms import MovieForm
from movies.models import Genre, Movie
from reviews.models import Review
from .decorators import admin_required

User = get_user_model()


@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(View):
    template_name = 'admin_panel/dashboard.html'

    def get(self, request):
        total_users = User.objects.count()
        total_movies = Movie.objects.count()
        total_reviews = Review.objects.count()
        positive_reviews = Review.objects.filter(sentiment='positive').count()
        negative_reviews = Review.objects.filter(sentiment='negative').count()
        neutral_reviews = Review.objects.filter(sentiment='neutral').count()

        top_movies = Movie.objects.order_by('-avg_rating', '-total_ratings')[:10]
        recent_users = User.objects.order_by('-date_joined')[:10]
        recent_reviews = Review.objects.select_related('user', 'movie').order_by('-created_at')[:10]

        context = {
            'total_users': total_users,
            'total_movies': total_movies,
            'total_reviews': total_reviews,
            'positive_reviews': positive_reviews,
            'negative_reviews': negative_reviews,
            'neutral_reviews': neutral_reviews,
            'top_movies': top_movies,
            'recent_users': recent_users,
            'recent_reviews': recent_reviews,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class UserManagementView(View):
    template_name = 'admin_panel/users.html'

    def get(self, request):
        users = User.objects.all().order_by('-date_joined')
        q = request.GET.get('q', '').strip()
        if q:
            users = users.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        paginator = Paginator(users, 25)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        context = {
            'page_obj': page_obj,
            'users': page_obj,
            'query': q,
            'total_count': paginator.count,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class ToggleUserActiveView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        # Prevent deactivating yourself or other superusers
        if user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
        elif user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Only superusers can deactivate other superusers.')
        else:
            user.is_active = not user.is_active
            user.save(update_fields=['is_active'])
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User "{user.username}" has been {status}.')
        return redirect('admin_panel:users')


@method_decorator(admin_required, name='dispatch')
class ToggleUserStaffView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, 'You cannot change your own staff status.')
        elif user.is_superuser:
            messages.error(request, 'Cannot change staff status of a superuser.')
        else:
            user.is_staff = not user.is_staff
            user.save(update_fields=['is_staff'])
            status = 'granted staff access' if user.is_staff else 'revoked staff access from'
            messages.success(request, f'Successfully {status} user "{user.username}".')
        return redirect('admin_panel:users')


@method_decorator(admin_required, name='dispatch')
class MovieManagementView(View):
    template_name = 'admin_panel/movies.html'

    def get(self, request):
        movies = Movie.objects.prefetch_related('genres').order_by('-id')
        q = request.GET.get('q', '').strip()
        genre_id = request.GET.get('genre_id')

        if q:
            movies = movies.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if genre_id:
            try:
                movies = movies.filter(genres__id=int(genre_id))
            except (ValueError, TypeError):
                pass

        movies = movies.distinct()
        paginator = Paginator(movies, 25)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        context = {
            'page_obj': page_obj,
            'movies': page_obj,
            'genres': Genre.objects.all().order_by('name'),
            'query': q,
            'total_count': paginator.count,
        }
        return render(request, self.template_name, context)


@method_decorator(admin_required, name='dispatch')
class AddMovieView(View):
    template_name = 'admin_panel/movie_form.html'

    def get(self, request):
        form = MovieForm()
        return render(request, self.template_name, {'form': form, 'action': 'Add'})

    def post(self, request):
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f'Movie "{movie.title}" added successfully.')
            return redirect('admin_panel:movies')
        return render(request, self.template_name, {'form': form, 'action': 'Add'})


@method_decorator(admin_required, name='dispatch')
class EditMovieView(View):
    template_name = 'admin_panel/movie_form.html'

    def get(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        form = MovieForm(instance=movie)
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'movie': movie})

    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f'Movie "{movie.title}" updated successfully.')
            return redirect('admin_panel:movies')
        return render(request, self.template_name, {'form': form, 'action': 'Edit', 'movie': movie})


@method_decorator(admin_required, name='dispatch')
class DeleteMovieView(View):
    template_name = 'admin_panel/movie_confirm_delete.html'

    def get(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        return render(request, self.template_name, {'movie': movie})

    def post(self, request, pk):
        movie = get_object_or_404(Movie, pk=pk)
        title = movie.title
        movie.delete()
        messages.success(request, f'Movie "{title}" deleted successfully.')
        return redirect('admin_panel:movies')


@method_decorator(admin_required, name='dispatch')
class RetrainView(View):
    template_name = 'admin_panel/retrain.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        results = {}

        # Get which model button was clicked
        model = request.POST.get('model', '').strip()

        # =========================
        # TRAIN SVD MODEL
        # =========================
        if model in ['svd', 'both']:
            try:
                from recommendations.engine import train_svd_model

                algo = train_svd_model()

                if algo is not None:
                    results['svd_status'] = True
                    results['svd_message'] = (
                        'SVD model trained successfully.'
                    )
                else:
                    results['svd_status'] = False
                    results['svd_message'] = (
                        'SVD training skipped: not enough data.'
                    )

            except Exception as e:
                results['svd_status'] = False
                results['svd_message'] = (
                    f'SVD training failed: {str(e)}'
                )

        # =========================
        # TRAIN SENTIMENT MODEL
        # =========================
        if model in ['sentiment', 'both']:
            from django.conf import settings

            dataset_path = str(
                settings.BASE_DIR / 'datasets' / 'imdb_reviews.csv'
            )

            try:
                from reviews.sentiment import train_sentiment_model

                accuracy = train_sentiment_model(dataset_path)

                if accuracy is not None:
                    results['sentiment_status'] = True
                    results['sentiment_message'] = (
                        f'Sentiment model trained successfully. '
                        f'Accuracy: {accuracy:.4f} '
                        f'({accuracy * 100:.2f}%)'
                    )
                else:
                    results['sentiment_status'] = False
                    results['sentiment_message'] = (
                        'Sentiment training failed. '
                        'Check dataset path and format.'
                    )

            except Exception as e:
                results['sentiment_status'] = False
                results['sentiment_message'] = (
                    f'Sentiment training failed: {str(e)}'
                )

        # =========================
        # NO MODEL SELECTED
        # =========================
        if model not in ['svd', 'sentiment', 'both']:
            messages.warning(
                request,
                'Please select a model to retrain.'
            )
            return render(request, self.template_name)

        return render(
            request,
            self.template_name,
            {'results': results}
        )