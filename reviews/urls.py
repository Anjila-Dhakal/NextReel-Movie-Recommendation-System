from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:movie_id>/', views.AddReviewView.as_view(), name='add'),
    path('delete/<int:pk>/', views.DeleteReviewView.as_view(), name='delete'),
]
