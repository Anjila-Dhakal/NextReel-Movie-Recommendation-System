from django.urls import path

from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.RecommendationView.as_view(), name='index'),
]
