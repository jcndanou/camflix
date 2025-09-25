"""
Views for ratings app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _

from apps.movies.models import Movie
from .models import Rating


@login_required
def rating_history_view(request):
    """User's rating history."""
    ratings = Rating.objects.filter(user=request.user).select_related('movie').order_by('-updated_at')

    context = {
        'ratings': ratings,
    }
    return render(request, 'ratings/history.html', context)


@login_required
def rate_movie(request, movie_id):
    """Rate a movie."""
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == 'POST':
        score = int(request.POST.get('score', 0))
        if 0 <= score <= 100:
            rating, created = Rating.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={'score': score}
            )

            # Calculate tier based on user's rating distribution
            # This is simplified - in production, you'd use a more sophisticated algorithm
            if score < 20:
                rating.tier = 'terrible'
            elif score < 40:
                rating.tier = 'bad'
            elif score < 55:
                rating.tier = 'mediocre'
            elif score < 70:
                rating.tier = 'decent'
            elif score < 85:
                rating.tier = 'good'
            elif score < 95:
                rating.tier = 'great'
            else:
                rating.tier = 'superb'

            rating.save()

            if created:
                messages.success(request, _('Your rating has been saved'))
            else:
                messages.success(request, _('Your rating has been updated'))
        else:
            messages.error(request, _('Invalid rating score'))

    return redirect('movies:detail', pk=movie.id)
