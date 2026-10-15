from django.urls import path

from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.MovieListView.as_view(), name='list'),
    path('<int:pk>/', views.MovieDetailView.as_view(), name='detail'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('<int:pk>/watchlist/', views.AddToWatchlistView.as_view(), name='watchlist'),
    path('<int:pk>/watch/', views.RecordWatchView.as_view(), name='watch'),
]
