"""
Rating and Review models for CamFlix.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
# from django.contrib.postgres.search import SearchVectorField
# from django.contrib.postgres.indexes import GinIndex
import uuid


class Rating(models.Model):
    """User rating for a movie (0-100 scale like Criticker)."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    score = models.IntegerField(
        _('score'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Rating score from 0 to 100')
    )

    # User's percentile tier (calculated based on their rating distribution)
    tier = models.CharField(
        _('tier'),
        max_length=20,
        choices=[
            ('terrible', _('Terrible (0-10%)')),
            ('bad', _('Bad (10-30%)')),
            ('mediocre', _('Mediocre (30-50%)')),
            ('decent', _('Decent (50-70%)')),
            ('good', _('Good (70-85%)')),
            ('great', _('Great (85-95%)')),
            ('superb', _('Superb (95-100%)')),
        ],
        blank=True
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ratings'
        unique_together = ('user', 'movie')
        verbose_name = _('rating')
        verbose_name_plural = _('ratings')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', 'movie']),
            models.Index(fields=['score']),
            models.Index(fields=['tier']),
            models.Index(fields=['-updated_at']),
        ]

    def __str__(self):
        return f"{self.user.username} rated {self.movie.title}: {self.score}/100"

    def save(self, *args, **kwargs):
        """Calculate tier before saving."""
        self.tier = self.calculate_tier()
        super().save(*args, **kwargs)

    def calculate_tier(self):
        """Calculate the tier based on user's rating distribution."""
        # Get all user ratings
        user_ratings = Rating.objects.filter(user=self.user).values_list('score', flat=True)
        if not user_ratings:
            return 'decent'

        # Calculate percentile
        scores_below = sum(1 for s in user_ratings if s < self.score)
        percentile = (scores_below / len(user_ratings)) * 100

        # Assign tier based on percentile
        if percentile < 10:
            return 'terrible'
        elif percentile < 30:
            return 'bad'
        elif percentile < 50:
            return 'mediocre'
        elif percentile < 70:
            return 'decent'
        elif percentile < 85:
            return 'good'
        elif percentile < 95:
            return 'great'
        else:
            return 'superb'

    @property
    def is_positive(self):
        """Check if rating is positive (>= 70)."""
        return self.score >= 70


class Review(models.Model):
    """User review for a movie."""

    MODERATION_STATUS = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('flagged', _('Flagged')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    movie = models.ForeignKey(
        'movies.Movie',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.OneToOneField(
        Rating,
        on_delete=models.CASCADE,
        related_name='review',
        null=True,
        blank=True
    )

    # Review content
    title = models.CharField(_('title'), max_length=200, blank=True)
    content = models.TextField(_('content'), max_length=5000)
    spoiler_warning = models.BooleanField(_('contains spoilers'), default=False)

    # Moderation
    moderation_status = models.CharField(
        _('moderation status'),
        max_length=20,
        choices=MODERATION_STATUS,
        default='pending'
    )
    moderation_notes = models.TextField(_('moderation notes'), blank=True)
    moderated_at = models.DateTimeField(_('moderated at'), null=True, blank=True)
    moderated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reviews'
    )

    # Engagement metrics
    likes_count = models.IntegerField(_('likes count'), default=0)
    dislikes_count = models.IntegerField(_('dislikes count'), default=0)
    comments_count = models.IntegerField(_('comments count'), default=0)

    # Full-text search (PostgreSQL only - commented for SQLite)
    # search_vector = SearchVectorField(null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('user', 'movie')
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'movie']),
            models.Index(fields=['moderation_status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['-likes_count']),
            # GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"Review by {self.user.username} for {self.movie.title}"

    @property
    def is_approved(self):
        """Check if review is approved."""
        return self.moderation_status == 'approved'

    @property
    def net_likes(self):
        """Calculate net likes (likes - dislikes)."""
        return self.likes_count - self.dislikes_count


class ReviewReaction(models.Model):
    """User reaction to a review (like/dislike)."""

    REACTION_TYPES = [
        ('like', _('Like')),
        ('dislike', _('Dislike')),
    ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='review_reactions'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    reaction_type = models.CharField(
        _('reaction type'),
        max_length=10,
        choices=REACTION_TYPES
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_reactions'
        unique_together = ('user', 'review')
        verbose_name = _('review reaction')
        verbose_name_plural = _('review reactions')
        indexes = [
            models.Index(fields=['review', 'reaction_type']),
        ]

    def __str__(self):
        return f"{self.user.username} {self.reaction_type}d {self.review}"

    def save(self, *args, **kwargs):
        """Update review reaction counts."""
        is_new = self.pk is None
        old_reaction = None

        if not is_new:
            old_reaction = ReviewReaction.objects.get(pk=self.pk).reaction_type

        super().save(*args, **kwargs)

        # Update counts on the review
        if is_new:
            if self.reaction_type == 'like':
                self.review.likes_count += 1
            else:
                self.review.dislikes_count += 1
        elif old_reaction != self.reaction_type:
            if old_reaction == 'like':
                self.review.likes_count -= 1
                self.review.dislikes_count += 1
            else:
                self.review.dislikes_count -= 1
                self.review.likes_count += 1

        self.review.save(update_fields=['likes_count', 'dislikes_count'])

    def delete(self, *args, **kwargs):
        """Update review reaction counts on delete."""
        if self.reaction_type == 'like':
            self.review.likes_count -= 1
        else:
            self.review.dislikes_count -= 1
        self.review.save(update_fields=['likes_count', 'dislikes_count'])
        super().delete(*args, **kwargs)


class ReviewComment(models.Model):
    """Comment on a review."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='review_comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(_('content'), max_length=1000)

    # Moderation
    is_flagged = models.BooleanField(_('is flagged'), default=False)
    is_hidden = models.BooleanField(_('is hidden'), default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_comments'
        verbose_name = _('review comment')
        verbose_name_plural = _('review comments')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['review']),
            models.Index(fields=['parent']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.review}"

    def save(self, *args, **kwargs):
        """Update review comment count."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.review.comments_count += 1
            self.review.save(update_fields=['comments_count'])

    def delete(self, *args, **kwargs):
        """Update review comment count on delete."""
        self.review.comments_count -= 1
        self.review.save(update_fields=['comments_count'])
        super().delete(*args, **kwargs)
