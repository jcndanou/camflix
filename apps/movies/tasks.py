"""
Celery tasks for movies app.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .services import TMDBService
from .models import Movie

logger = logging.getLogger(__name__)


@shared_task
def sync_trending_movies():
    """Sync trending movies from TMDB."""
    try:
        tmdb = TMDBService()
        movies = tmdb.get_trending_movies('week')

        imported = 0
        for movie_data in movies:
            try:
                detailed_data = tmdb.get_movie_details(movie_data['id'])
                if tmdb.create_or_update_movie(detailed_data):
                    imported += 1
            except Exception as e:
                logger.error(f"Failed to import trending movie {movie_data['id']}: {e}")
                continue

        logger.info(f"Synchronized {imported} trending movies")
        return f"Imported {imported} trending movies"

    except Exception as e:
        logger.error(f"Failed to sync trending movies: {e}")
        raise


@shared_task
def sync_popular_movies():
    """Sync popular movies from TMDB."""
    try:
        tmdb = TMDBService()
        movies = tmdb.get_popular_movies(page=1)

        imported = 0
        for movie_data in movies:
            try:
                detailed_data = tmdb.get_movie_details(movie_data['id'])
                if tmdb.create_or_update_movie(detailed_data):
                    imported += 1
            except Exception as e:
                logger.error(f"Failed to import popular movie {movie_data['id']}: {e}")
                continue

        logger.info(f"Synchronized {imported} popular movies")
        return f"Imported {imported} popular movies"

    except Exception as e:
        logger.error(f"Failed to sync popular movies: {e}")
        raise


@shared_task
def update_recent_movie_details():
    """Update details for recently viewed movies."""
    try:
        # Get movies viewed in the last 7 days
        recent_date = timezone.now() - timedelta(days=7)
        movies = Movie.objects.filter(
            ratings__created_at__gte=recent_date
        ).distinct()[:20]

        tmdb = TMDBService()
        updated = 0

        for movie in movies:
            try:
                detailed_data = tmdb.get_movie_details(movie.tmdb_id)
                if tmdb.create_or_update_movie(detailed_data):
                    updated += 1
            except Exception as e:
                logger.error(f"Failed to update movie {movie.tmdb_id}: {e}")
                continue

        logger.info(f"Updated {updated} recent movies")
        return f"Updated {updated} movies"

    except Exception as e:
        logger.error(f"Failed to update recent movies: {e}")
        raise


@shared_task
def import_movie_details(tmdb_id: int):
    """Import detailed information for a specific movie."""
    try:
        tmdb = TMDBService()
        detailed_data = tmdb.get_movie_details(tmdb_id)
        movie = tmdb.create_or_update_movie(detailed_data)

        if movie:
            logger.info(f"Imported movie: {movie.title} (TMDB ID: {tmdb_id})")
            return f"Imported {movie.title}"
        else:
            raise Exception(f"Failed to import movie with TMDB ID: {tmdb_id}")

    except Exception as e:
        logger.error(f"Failed to import movie {tmdb_id}: {e}")
        raise


@shared_task
def sync_genres():
    """Synchronize movie genres from TMDB."""
    try:
        tmdb = TMDBService()
        tmdb.sync_genres()
        return "Genres synchronized successfully"
    except Exception as e:
        logger.error(f"Failed to sync genres: {e}")
        raise