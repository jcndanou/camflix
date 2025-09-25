"""
Movie models for CamFlix.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
# from django.contrib.postgres.indexes import GinIndex
# from django.contrib.postgres.search import SearchVectorField
import uuid


class Genre(models.Model):
    """Movie genre from TMDB."""

    tmdb_id = models.IntegerField(_('TMDB ID'), unique=True)
    name = models.CharField(_('name'), max_length=100)
    name_fr = models.CharField(_('name (French)'), max_length=100, blank=True)

    class Meta:
        db_table = 'genres'
        verbose_name = _('genre')
        verbose_name_plural = _('genres')
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_localized_name(self, language='en'):
        """Return localized genre name."""
        if language == 'fr' and self.name_fr:
            return self.name_fr
        return self.name


class Person(models.Model):
    """Person (actor, director, etc.) from TMDB."""

    PERSON_TYPES = [
        ('actor', _('Actor')),
        ('director', _('Director')),
        ('producer', _('Producer')),
        ('writer', _('Writer')),
    ]

    tmdb_id = models.IntegerField(_('TMDB ID'), unique=True)
    name = models.CharField(_('name'), max_length=255)
    biography = models.TextField(_('biography'), blank=True)
    birthday = models.DateField(_('birthday'), null=True, blank=True)
    deathday = models.DateField(_('deathday'), null=True, blank=True)
    place_of_birth = models.CharField(_('place of birth'), max_length=255, blank=True)
    profile_path = models.CharField(_('profile path'), max_length=255, blank=True)
    popularity = models.FloatField(_('popularity'), default=0)
    person_type = models.CharField(
        _('person type'),
        max_length=20,
        choices=PERSON_TYPES,
        default='actor'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'persons'
        verbose_name = _('person')
        verbose_name_plural = _('persons')
        ordering = ['-popularity', 'name']
        indexes = [
            models.Index(fields=['tmdb_id']),
            models.Index(fields=['name']),
            models.Index(fields=['-popularity']),
        ]

    def __str__(self):
        return self.name

    @property
    def profile_url(self):
        """Return full URL for profile image."""
        if self.profile_path:
            return f"https://image.tmdb.org/t/p/w500{self.profile_path}"
        return None


class Movie(models.Model):
    """Movie model with TMDB data."""

    # TMDB fields
    tmdb_id = models.IntegerField(_('TMDB ID'), unique=True, db_index=True)
    imdb_id = models.CharField(_('IMDB ID'), max_length=20, blank=True, db_index=True)
    title = models.CharField(_('title'), max_length=500)
    original_title = models.CharField(_('original title'), max_length=500)
    title_fr = models.CharField(_('title (French)'), max_length=500, blank=True)

    # Content
    overview = models.TextField(_('overview'), blank=True)
    overview_fr = models.TextField(_('overview (French)'), blank=True)
    tagline = models.CharField(_('tagline'), max_length=500, blank=True)

    # Dates
    release_date = models.DateField(_('release date'), null=True, blank=True)
    runtime = models.IntegerField(_('runtime'), null=True, blank=True, help_text=_('Runtime in minutes'))

    # Media
    poster_path = models.CharField(_('poster path'), max_length=255, blank=True)
    backdrop_path = models.CharField(_('backdrop path'), max_length=255, blank=True)

    # Metrics
    popularity = models.FloatField(_('popularity'), default=0)
    vote_average = models.FloatField(
        _('vote average'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    vote_count = models.IntegerField(_('vote count'), default=0)
    budget = models.BigIntegerField(_('budget'), default=0)
    revenue = models.BigIntegerField(_('revenue'), default=0)

    # Relations
    genres = models.ManyToManyField(Genre, related_name='movies', blank=True)
    directors = models.ManyToManyField(
        Person,
        related_name='directed_movies',
        blank=True,
        limit_choices_to={'person_type': 'director'}
    )
    actors = models.ManyToManyField(
        Person,
        through='MovieCast',
        related_name='acted_in_movies',
        blank=True
    )

    # Additional info
    original_language = models.CharField(_('original language'), max_length=10, default='en')
    adult = models.BooleanField(_('adult content'), default=False)
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=[
            ('Released', _('Released')),
            ('Upcoming', _('Upcoming')),
            ('In Production', _('In Production')),
            ('Canceled', _('Canceled')),
        ],
        default='Released'
    )

    # Full-text search (PostgreSQL only - commented for SQLite)
    # search_vector = SearchVectorField(null=True)

    # Cache control
    last_tmdb_sync = models.DateTimeField(_('last TMDB sync'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies'
        verbose_name = _('movie')
        verbose_name_plural = _('movies')
        ordering = ['-popularity', '-release_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['-popularity']),
            models.Index(fields=['-vote_average']),
            models.Index(fields=['tmdb_id']),
            # GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        year = self.release_date.year if self.release_date else 'N/A'
        return f"{self.title} ({year})"

    @property
    def poster_url(self):
        """Return full URL for poster image."""
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return None

    @property
    def backdrop_url(self):
        """Return full URL for backdrop image."""
        if self.backdrop_path:
            return f"https://image.tmdb.org/t/p/original{self.backdrop_path}"
        return None

    @property
    def year(self):
        """Return release year."""
        return self.release_date.year if self.release_date else None

    @property
    def average_rating(self):
        """Calculate average rating from user ratings."""
        from django.db.models import Avg
        avg = self.ratings.aggregate(Avg('score'))['score__avg']
        return round(avg, 1) if avg else 0

    @property
    def rating_count(self):
        """Return number of user ratings."""
        return self.ratings.count()

    def get_localized_title(self, language='en'):
        """Return localized movie title."""
        if language == 'fr' and self.title_fr:
            return self.title_fr
        return self.title

    def get_localized_overview(self, language='en'):
        """Return localized movie overview."""
        if language == 'fr' and self.overview_fr:
            return self.overview_fr
        return self.overview


class MovieCast(models.Model):
    """Movie cast relationship with character and order."""

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='cast')
    actor = models.ForeignKey(Person, on_delete=models.CASCADE)
    character = models.CharField(_('character'), max_length=255, blank=True)
    order = models.IntegerField(_('order'), default=0)

    class Meta:
        db_table = 'movie_cast'
        unique_together = ('movie', 'actor', 'character')
        ordering = ['order']
        verbose_name = _('movie cast')
        verbose_name_plural = _('movie casts')

    def __str__(self):
        return f"{self.actor.name} as {self.character} in {self.movie.title}"


class MovieList(models.Model):
    """User-created movie lists."""

    LIST_TYPES = [
        ('watchlist', _('Watchlist')),
        ('favorites', _('Favorites')),
        ('custom', _('Custom')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='movie_lists'
    )
    name = models.CharField(_('name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    list_type = models.CharField(
        _('list type'),
        max_length=20,
        choices=LIST_TYPES,
        default='custom'
    )
    is_public = models.BooleanField(_('public'), default=False)
    movies = models.ManyToManyField(
        Movie,
        through='MovieListItem',
        related_name='in_lists'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movie_lists'
        unique_together = ('user', 'name')
        verbose_name = _('movie list')
        verbose_name_plural = _('movie lists')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'list_type']),
            models.Index(fields=['is_public']),
        ]

    def __str__(self):
        return f"{self.user.username}'s {self.name}"

    @property
    def movie_count(self):
        """Return number of movies in the list."""
        return self.movies.count()


class MovieListItem(models.Model):
    """Item in a movie list with ordering."""

    movie_list = models.ForeignKey(MovieList, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    order = models.IntegerField(_('order'), default=0)
    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True)

    class Meta:
        db_table = 'movie_list_items'
        unique_together = ('movie_list', 'movie')
        ordering = ['order', '-added_at']
        verbose_name = _('movie list item')
        verbose_name_plural = _('movie list items')

    def __str__(self):
        return f"{self.movie.title} in {self.movie_list.name}"


class Comment(models.Model):
    """User comments on movies."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='movie_comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Content
    content = models.TextField(_('content'), max_length=2000)
    is_spoiler = models.BooleanField(_('contains spoilers'), default=False)

    # Moderation
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movie_comments'
        ordering = ['-created_at']
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        indexes = [
            models.Index(fields=['movie', '-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.movie.title}"

    @property
    def like_count(self):
        """Return number of likes for this comment."""
        return self.likes.filter(is_like=True).count()

    @property
    def dislike_count(self):
        """Return number of dislikes for this comment."""
        return self.likes.filter(is_like=False).count()

    @property
    def reply_count(self):
        """Return number of replies."""
        return self.replies.filter(is_deleted=False).count()

    def get_user_reaction(self, user):
        """Get user's reaction to this comment."""
        if not user.is_authenticated:
            return None
        try:
            reaction = self.likes.get(user=user)
            return 'like' if reaction.is_like else 'dislike'
        except CommentLike.DoesNotExist:
            return None


class CommentLike(models.Model):
    """Like/dislike reactions for comments."""

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='comment_likes'
    )
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_likes'
        unique_together = ('comment', 'user')
        verbose_name = _('comment like')
        verbose_name_plural = _('comment likes')

    def __str__(self):
        action = "liked" if self.is_like else "disliked"
        return f"{self.user.username} {action} comment on {self.comment.movie.title}"
