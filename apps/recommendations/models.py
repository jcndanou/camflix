"""
Recommendation models for CamFlix.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
# from django.contrib.postgres.fields import ArrayField
import uuid
import json


class UserSimilarity(models.Model):
    """Store similarity scores between users for collaborative filtering."""

    user1 = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='similarities_as_user1'
    )
    user2 = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='similarities_as_user2'
    )
    similarity_score = models.FloatField(
        _('similarity score'),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text=_('Similarity score between 0 and 1')
    )
    common_movies_count = models.IntegerField(
        _('common movies count'),
        default=0,
        help_text=_('Number of movies both users have rated')
    )

    # Calculation metadata
    calculation_method = models.CharField(
        _('calculation method'),
        max_length=50,
        choices=[
            ('pearson', _('Pearson Correlation')),
            ('cosine', _('Cosine Similarity')),
            ('euclidean', _('Euclidean Distance')),
            ('jaccard', _('Jaccard Index')),
        ],
        default='pearson'
    )

    # Timestamps
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_similarities'
        unique_together = ('user1', 'user2')
        verbose_name = _('user similarity')
        verbose_name_plural = _('user similarities')
        indexes = [
            models.Index(fields=['user1', 'user2']),
            models.Index(fields=['-similarity_score']),
            models.Index(fields=['calculated_at']),
        ]

    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username}: {self.similarity_score:.2f}"

    def save(self, *args, **kwargs):
        """Ensure user1.id < user2.id for consistency."""
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)


class Recommendation(models.Model):
    """Movie recommendations for users."""

    RECOMMENDATION_TYPES = [
        ('collaborative', _('Collaborative Filtering')),
        ('content', _('Content-Based')),
        ('hybrid', _('Hybrid')),
        ('trending', _('Trending')),
        ('genre', _('Genre-Based')),
        ('director', _('Director-Based')),
        ('actor', _('Actor-Based')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='recommendations'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='recommended_to'
    )

    # Recommendation metadata
    recommendation_type = models.CharField(
        _('recommendation type'),
        max_length=20,
        choices=RECOMMENDATION_TYPES,
        default='hybrid'
    )
    confidence_score = models.FloatField(
        _('confidence score'),
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text=_('Confidence in the recommendation (0-1)')
    )
    predicted_rating = models.FloatField(
        _('predicted rating'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Predicted rating (0-100)')
    )

    # Explanation for the recommendation
    reason = models.TextField(
        _('reason'),
        blank=True,
        help_text=_('Explanation for why this movie was recommended')
    )
    # PostgreSQL ArrayField - Using JSONField for SQLite compatibility
    similar_users = models.JSONField(
        default=list,
        blank=True,
        help_text=_('IDs of similar users who liked this movie')
    )

    # User interaction
    is_seen = models.BooleanField(_('is seen'), default=False)
    is_dismissed = models.BooleanField(_('is dismissed'), default=False)
    user_feedback = models.CharField(
        _('user feedback'),
        max_length=20,
        choices=[
            ('helpful', _('Helpful')),
            ('not_helpful', _('Not Helpful')),
            ('already_seen', _('Already Seen')),
            ('not_interested', _('Not Interested')),
        ],
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'), null=True, blank=True)

    class Meta:
        db_table = 'recommendations'
        unique_together = ('user', 'movie')
        verbose_name = _('recommendation')
        verbose_name_plural = _('recommendations')
        ordering = ['-confidence_score', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_seen', 'is_dismissed']),
            models.Index(fields=['-confidence_score']),
            models.Index(fields=['recommendation_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"Recommend {self.movie.title} to {self.user.username} ({self.confidence_score:.2f})"

    @property
    def is_active(self):
        """Check if recommendation is still active."""
        from django.utils import timezone
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return not self.is_dismissed and not self.is_seen


class RecommendationProfile(models.Model):
    """User's recommendation profile with computed preferences."""

    user = models.OneToOneField(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='recommendation_profile'
    )

    # Computed genre preferences (normalized scores)
    genre_preferences = models.JSONField(
        _('genre preferences'),
        default=dict,
        help_text=_('Computed genre preference scores')
    )

    # Computed director preferences
    director_preferences = models.JSONField(
        _('director preferences'),
        default=dict,
        help_text=_('Computed director preference scores')
    )

    # Computed actor preferences
    actor_preferences = models.JSONField(
        _('actor preferences'),
        default=dict,
        help_text=_('Computed actor preference scores')
    )

    # Rating statistics
    average_rating = models.FloatField(
        _('average rating'),
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    rating_std_dev = models.FloatField(
        _('rating standard deviation'),
        default=0,
        validators=[MinValueValidator(0)]
    )

    # Tier distribution
    tier_distribution = models.JSONField(
        _('tier distribution'),
        default=dict,
        help_text=_('Distribution of user ratings across tiers')
    )

    # Similar users cache
    similar_users = models.JSONField(
        _('similar users'),
        default=list,
        help_text=_('List of most similar user IDs with scores')
    )

    # Timestamps
    last_calculated = models.DateTimeField(_('last calculated'), auto_now=True)

    class Meta:
        db_table = 'recommendation_profiles'
        verbose_name = _('recommendation profile')
        verbose_name_plural = _('recommendation profiles')

    def __str__(self):
        return f"{self.user.username}'s recommendation profile"

    def update_preferences(self):
        """Update user preferences based on their ratings."""
        from django.db.models import Avg, StdDev, Count
        from apps.ratings.models import Rating

        # Update rating statistics
        stats = Rating.objects.filter(user=self.user).aggregate(
            avg=Avg('score'),
            std=StdDev('score')
        )
        self.average_rating = stats['avg'] or 0
        self.rating_std_dev = stats['std'] or 0

        # Update genre preferences
        genre_scores = {}
        ratings = Rating.objects.filter(user=self.user).select_related('movie').prefetch_related('movie__genres')

        for rating in ratings:
            for genre in rating.movie.genres.all():
                if genre.name not in genre_scores:
                    genre_scores[genre.name] = []
                genre_scores[genre.name].append(rating.score)

        self.genre_preferences = {
            genre: sum(scores) / len(scores)
            for genre, scores in genre_scores.items()
        }

        # Update tier distribution
        tier_counts = Rating.objects.filter(user=self.user).values('tier').annotate(count=Count('tier'))
        self.tier_distribution = {item['tier']: item['count'] for item in tier_counts}

        self.save()


class RecommendationBatch(models.Model):
    """Batch of recommendations generated together."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='recommendation_batches'
    )

    # Batch metadata
    batch_size = models.IntegerField(_('batch size'), default=0)
    algorithm_version = models.CharField(_('algorithm version'), max_length=50)
    parameters = models.JSONField(
        _('parameters'),
        default=dict,
        help_text=_('Parameters used for generating this batch')
    )

    # Performance metrics
    generation_time = models.FloatField(
        _('generation time'),
        help_text=_('Time taken to generate recommendations in seconds')
    )
    accuracy_score = models.FloatField(
        _('accuracy score'),
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text=_('Measured accuracy of recommendations if available')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recommendation_batches'
        verbose_name = _('recommendation batch')
        verbose_name_plural = _('recommendation batches')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Batch for {self.user.username} at {self.created_at}"
