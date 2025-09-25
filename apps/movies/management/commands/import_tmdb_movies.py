"""
Django management command to import movies from TMDB API.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from apps.movies.services import TMDBService
import time


class Command(BaseCommand):
    help = 'Import movies from The Movie Database (TMDB) API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='popular',
            choices=['popular', 'top_rated', 'trending'],
            help='Type of movies to import'
        )
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to import (20 movies per page)'
        )
        parser.add_argument(
            '--sync-genres',
            action='store_true',
            help='Synchronize genres before importing movies'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Delay between API calls in seconds'
        )

    def handle(self, *args, **options):
        if not settings.TMDB_API_KEY:
            self.stdout.write(
                self.style.ERROR('TMDB_API_KEY is not configured in settings')
            )
            self.stdout.write(
                self.style.WARNING(
                    'Please add your TMDB API key to your .env file:\n'
                    'TMDB_API_KEY=your_api_key_here\n\n'
                    'You can get a free API key at https://www.themoviedb.org/settings/api'
                )
            )
            return

        tmdb = TMDBService()

        # Sync genres if requested
        if options['sync_genres']:
            self.stdout.write('Synchronizing genres...')
            try:
                tmdb.sync_genres()
                self.stdout.write(self.style.SUCCESS('Genres synchronized successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to sync genres: {e}'))

        # Import movies
        movie_type = options['type']
        pages = options['pages']
        delay = options['delay']

        self.stdout.write(f'Importing {movie_type} movies ({pages} pages)...')

        try:
            # Set delay for API rate limiting
            if delay > 0:
                self.stdout.write(f'Using {delay}s delay between API calls')
                # Monkey-patch the service to add delay
                original_make_request = tmdb._make_request

                def delayed_request(*args, **kwargs):
                    result = original_make_request(*args, **kwargs)
                    time.sleep(delay)
                    return result

                tmdb._make_request = delayed_request

            imported = tmdb.import_movies_batch(movie_type=movie_type, pages=pages)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {imported} movies from TMDB'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {e}'))
            raise