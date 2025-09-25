"""
URL configuration for ratings app.
"""

from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('history/', views.rating_history_view, name='history'),
    path('rate/<int:movie_id>/', views.rate_movie, name='rate'),
]