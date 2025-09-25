"""
Celery configuration for CamFlix project.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.local')

app = Celery('camflix')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Sync trending movies daily at 2 AM
    'sync-trending-movies': {
        'task': 'apps.movies.tasks.sync_trending_movies',
        'schedule': crontab(hour=2, minute=0),
    },
    # Sync popular movies daily at 3 AM
    'sync-popular-movies': {
        'task': 'apps.movies.tasks.sync_popular_movies',
        'schedule': crontab(hour=3, minute=0),
    },
    # Update movie details for recently viewed movies
    'update-movie-details': {
        'task': 'apps.movies.tasks.update_recent_movie_details',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    # Calculate user similarities for recommendations
    'calculate-user-similarities': {
        'task': 'apps.recommendations.tasks.calculate_all_user_similarities',
        'schedule': crontab(hour='*/4'),  # Every 4 hours
    },
    # Clean up old recommendation cache
    'cleanup-recommendations-cache': {
        'task': 'apps.recommendations.tasks.cleanup_old_recommendations',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM
    },
    # Send email notifications for new recommendations
    'send-recommendation-emails': {
        'task': 'apps.recommendations.tasks.send_weekly_recommendations',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Monday at 9 AM
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')