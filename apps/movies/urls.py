"""
URL configuration for movies app.
"""

from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.MovieListView.as_view(), name='list'),
    path('<int:pk>/', views.MovieDetailView.as_view(), name='detail'),
    path('trending/', views.trending_view, name='trending'),
    path('top-rated/', views.top_rated_view, name='top-rated'),
    path('genres/', views.genres_view, name='genres'),
    path('search/', views.search_view, name='search'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('<int:movie_id>/add-to-watchlist/', views.add_to_watchlist, name='add-to-watchlist'),
    path('<int:movie_id>/remove-from-watchlist/', views.remove_from_watchlist, name='remove-from-watchlist'),

    # Comment URLs
    path('<int:movie_id>/comment/', views.add_comment, name='add-comment'),
    path('comment/<uuid:comment_id>/edit/', views.edit_comment, name='edit-comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete-comment'),
    path('comment/<uuid:comment_id>/like/', views.toggle_comment_like, name='toggle-comment-like'),
]