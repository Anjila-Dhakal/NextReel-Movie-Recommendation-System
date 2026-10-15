from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from movies.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('users/', include('users.urls', namespace='users')),
    path('movies/', include('movies.urls', namespace='movies')),
    path('recommendations/', include('recommendations.urls', namespace='recommendations')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
