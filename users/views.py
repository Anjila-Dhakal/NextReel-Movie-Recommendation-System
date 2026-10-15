


from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import FormView

from .forms import ProfileEditForm, RegisterForm
from .models import CustomUser


class RegisterView(FormView):
    template_name = 'users/register.html'
    form_class = RegisterForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome to NextReel, {user.username}!')
        return redirect('home')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class LoginView(View):
    template_name = 'users/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(
                request,
                f'Welcome back, {user.username}!'
            )

            return redirect('recommendations:index')

        return render(
            request,
            self.template_name,
            {'form': form}
        )
class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('home')

    def get(self, request):
        # Allow GET logout as well for convenience
        logout(request)
        return redirect('home')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'
    login_url = '/users/login/'

    def get(self, request):
        from reviews.models import Review
        from movies.models import Watchlist, WatchHistory

        reviews = Review.objects.filter(user=request.user).select_related('movie').order_by('-created_at')[:20]
        watchlist = Watchlist.objects.filter(user=request.user).select_related('movie').order_by('-added_at')[:20]
        watch_history = WatchHistory.objects.filter(user=request.user).select_related('movie').order_by('-watched_at')[:20]
        total_reviews = Review.objects.filter(user=request.user).count()
        positive_count = Review.objects.filter(user=request.user, sentiment='positive').count()
        negative_count = Review.objects.filter(user=request.user, sentiment='negative').count()

        context = {
            'profile_user': request.user,
            'reviews': reviews,
            'watchlist': watchlist,
            'watch_history': watch_history,
            'total_reviews': total_reviews,
            'positive_count': positive_count,
            'negative_count': negative_count,
        }
        return render(request, self.template_name, context)


class ProfileEditView(LoginRequiredMixin, View):
    template_name = 'users/edit_profile.html'
    login_url = '/users/login/'

    def get(self, request):
        form = ProfileEditForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
        return render(request, self.template_name, {'form': form})


class SetThemeView(LoginRequiredMixin, View):
    login_url = '/users/login/'

    def post(self, request):
        theme = request.POST.get('theme', 'dark')
        if theme not in ['dark', 'warm']:
            return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
        request.user.theme_preference = theme
        request.user.save(update_fields=['theme_preference'])
        return JsonResponse({'status': 'ok', 'theme': theme})
