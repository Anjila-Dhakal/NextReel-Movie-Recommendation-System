from django.urls import path

from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.UserManagementView.as_view(), name='users'),
    path('movies/', views.MovieManagementView.as_view(), name='movies'),
    path('movies/add/', views.AddMovieView.as_view(), name='add_movie'),
    path('movies/edit/<int:pk>/', views.EditMovieView.as_view(), name='edit_movie'),
    path('movies/delete/<int:pk>/', views.DeleteMovieView.as_view(), name='delete_movie'),
    path('retrain/', views.RetrainView.as_view(), name='retrain'),
    path('users/<int:pk>/toggle-active/', views.ToggleUserActiveView.as_view(), name='toggle_active'),
    path('users/<int:pk>/toggle-staff/', views.ToggleUserStaffView.as_view(), name='toggle_staff'),
]
