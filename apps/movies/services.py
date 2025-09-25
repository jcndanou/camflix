"""
TMDB API integration service.
"""

import requests
from django.conf import settings
from django.utils import timezone
from typing import Dict, List, Optional
import logging

from .models import Movie, Genre, Person, MovieCast

logger = logging.getLogger(__name__)


class TMDBService:
    """Service for interacting with The Movie Database API."""

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_API_BASE_URL
        self.headers = {
            'Accept': 'application/json',
        }

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request to the TMDB API."""
        if not self.api_key:
            raise ValueError("TMDB_API_KEY is not configured")

        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        params['language'] = 'fr-FR'

        try:
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB API request failed: {e}")
            raise

    def get_genres(self) -> List[Dict]:
        """Get list of movie genres from TMDB."""
        data = self._make_request('/genre/movie/list')
        return data.get('genres', [])

    def sync_genres(self):
        """Synchronize genres with TMDB."""
        genres = self.get_genres()

        for genre_data in genres:
            Genre.objects.update_or_create(
                tmdb_id=genre_data['id'],
                defaults={
                    'name': genre_data['name'],
                    'name_fr': genre_data['name'],
                }
            )

        logger.info(f"Synchronized {len(genres)} genres from TMDB")

    def get_trending_movies(self, time_window: str = 'week') -> List[Dict]:
        """Get trending movies from TMDB."""
        data = self._make_request(f'/trending/movie/{time_window}')
        return data.get('results', [])

    def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """Get popular movies from TMDB."""
        data = self._make_request('/movie/popular', params={'page': page})
        return data.get('results', [])

    def get_top_rated_movies(self, page: int = 1) -> List[Dict]:
        """Get top rated movies from TMDB."""
        data = self._make_request('/movie/top_rated', params={'page': page})
        return data.get('results', [])

    def get_movie_details(self, tmdb_id: int) -> Dict:
        """Get detailed information about a movie."""
        return self._make_request(
            f'/movie/{tmdb_id}',
            params={'append_to_response': 'credits,videos,images,translations'}
        )

    def create_or_update_movie(self, movie_data: Dict) -> Optional[Movie]:
        """Create or update a movie from TMDB data."""
        try:
            # Get French translation
            translations = movie_data.get('translations', {}).get('translations', [])
            french_translation = next(
                (t['data'] for t in translations if t['iso_3166_1'] == 'FR'),
                {}
            )

            # Basic movie data
            movie_defaults = {
                'title': movie_data['title'],
                'original_title': movie_data.get('original_title', movie_data['title']),
                'title_fr': french_translation.get('title', movie_data['title']),
                'overview': movie_data.get('overview', ''),
                'overview_fr': french_translation.get('overview', movie_data.get('overview', '')),
                'tagline': movie_data.get('tagline', ''),
                'release_date': movie_data.get('release_date') or None,
                'runtime': movie_data.get('runtime') or None,
                'poster_path': movie_data.get('poster_path', ''),
                'backdrop_path': movie_data.get('backdrop_path', ''),
                'popularity': movie_data.get('popularity', 0),
                'vote_average': movie_data.get('vote_average', 0),
                'vote_count': movie_data.get('vote_count', 0),
                'budget': movie_data.get('budget', 0),
                'revenue': movie_data.get('revenue', 0),
                'imdb_id': movie_data.get('imdb_id', ''),
                'original_language': movie_data.get('original_language', 'en'),
                'adult': movie_data.get('adult', False),
                'status': movie_data.get('status', 'Released'),
                'last_tmdb_sync': timezone.now(),
            }

            movie, created = Movie.objects.update_or_create(
                tmdb_id=movie_data['id'],
                defaults=movie_defaults
            )

            # Sync genres
            if 'genres' in movie_data:
                genre_ids = []
                for genre_data in movie_data['genres']:
                    genre, _ = Genre.objects.get_or_create(
                        tmdb_id=genre_data['id'],
                        defaults={'name': genre_data['name'], 'name_fr': genre_data['name']}
                    )
                    genre_ids.append(genre.id)
                movie.genres.set(genre_ids)

            # Sync cast
            if 'credits' in movie_data:
                self._sync_movie_cast(movie, movie_data['credits'])

            action = "Created" if created else "Updated"
            logger.info(f"{action} movie: {movie.title} (TMDB ID: {movie.tmdb_id})")

            return movie

        except Exception as e:
            logger.error(f"Failed to create/update movie {movie_data.get('id')}: {e}")
            return None

    def _sync_movie_cast(self, movie: Movie, credits: Dict):
        """Sync movie cast and crew."""
        # Sync directors
        directors = []
        for crew_member in credits.get('crew', [])[:10]:
            if crew_member['job'] == 'Director':
                person, _ = Person.objects.update_or_create(
                    tmdb_id=crew_member['id'],
                    defaults={
                        'name': crew_member['name'],
                        'profile_path': crew_member.get('profile_path') or '',
                        'person_type': 'director',
                    }
                )
                directors.append(person)

        if directors:
            movie.directors.set(directors)

        # Sync cast
        MovieCast.objects.filter(movie=movie).delete()

        for index, cast_member in enumerate(credits.get('cast', [])[:20]):
            person, _ = Person.objects.update_or_create(
                tmdb_id=cast_member['id'],
                defaults={
                    'name': cast_member['name'],
                    'profile_path': cast_member.get('profile_path') or '',
                    'person_type': 'actor',
                }
            )

            MovieCast.objects.create(
                movie=movie,
                actor=person,
                character=cast_member.get('character', ''),
                order=cast_member.get('order', index)
            )

    def import_movies_batch(self, movie_type: str = 'popular', pages: int = 5):
        """Import a batch of movies from TMDB."""
        imported = 0

        for page in range(1, pages + 1):
            if movie_type == 'popular':
                movies = self.get_popular_movies(page)
            elif movie_type == 'top_rated':
                movies = self.get_top_rated_movies(page)
            elif movie_type == 'trending':
                movies = self.get_trending_movies()
            else:
                raise ValueError(f"Unknown movie type: {movie_type}")

            for movie_data in movies:
                # Get detailed information
                try:
                    detailed_data = self.get_movie_details(movie_data['id'])
                    if self.create_or_update_movie(detailed_data):
                        imported += 1
                except Exception as e:
                    logger.error(f"Failed to import movie {movie_data['id']}: {e}")
                    continue

        logger.info(f"Imported {imported} movies from TMDB")
        return imported