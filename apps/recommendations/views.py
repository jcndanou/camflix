"""
Views for recommendations app.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q

from apps.movies.models import Movie
from apps.ratings.models import Rating
from .models import Recommendation


@login_required
def for_you_view(request):
    """Personalized recommendations for the user."""
    user = request.user

    # Get user's rated movies
    user_ratings = Rating.objects.filter(user=user).values_list('movie_id', flat=True)

    # Simple recommendation algorithm:
    # 1. Find movies with similar genres to highly rated movies
    # 2. Exclude already rated movies
    # 3. Sort by popularity and rating

    if user_ratings:
        # Get genres from user's highly rated movies (score >= 70)
        preferred_genres = Rating.objects.filter(
            user=user,
            score__gte=70
        ).values_list('movie__genres', flat=True).distinct()

        # Get recommendations based on genres
        recommended_movies = Movie.objects.filter(
            genres__in=preferred_genres
        ).exclude(
            id__in=user_ratings
        ).annotate(
            avg_rating=Avg('ratings__score'),
            rating_count=Count('ratings')
        ).filter(
            rating_count__gte=5
        ).order_by('-avg_rating', '-popularity').distinct()[:24]
    else:
        # For new users, show popular movies
        recommended_movies = Movie.objects.order_by('-popularity')[:24]

    # Get existing recommendations
    recommendations = Recommendation.objects.filter(
        user=user
    ).select_related('movie').order_by('-confidence_score')[:12]

    context = {
        'recommended_movies': recommended_movies,
        'recommendations': recommendations,
    }
    return render(request, 'recommendations/for_you.html', context)
