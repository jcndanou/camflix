"""
User models for CamFlix.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser."""

    email = models.EmailField(_('email address'), unique=True)
    bio = models.TextField(_('biography'), max_length=500, blank=True)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True
    )
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    preferred_language = models.CharField(
        _('preferred language'),
        max_length=10,
        choices=[('fr', 'Français'), ('en', 'English')],
        default='fr'
    )

    # Profile completion
    is_profile_complete = models.BooleanField(default=False)

    # Email notifications
    email_notifications = models.BooleanField(
        _('email notifications'),
        default=True,
        help_text=_('Receive email notifications for recommendations and updates')
    )

    # Timestamps
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return self.username

    @property
    def display_name(self):
        """Return the user's display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def rating_count(self):
        """Return the number of ratings by this user."""
        return self.ratings.count()

    @property
    def review_count(self):
        """Return the number of reviews by this user."""
        return self.reviews.count()

    def check_profile_completion(self):
        """Check and update profile completion status."""
        required_fields = ['first_name', 'last_name', 'bio', 'birth_date']
        self.is_profile_complete = all(getattr(self, field) for field in required_fields)
        self.save(update_fields=['is_profile_complete'])
        return self.is_profile_complete


class UserPreferences(models.Model):
    """User preferences for movie recommendations."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    # Genre preferences (will link to Genre model)
    favorite_genres = models.ManyToManyField(
        'movies.Genre',
        blank=True,
        related_name='preferred_by_users'
    )

    # Recommendation settings
    min_rating_for_recommendation = models.IntegerField(
        _('minimum rating for recommendation'),
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Minimum rating (0-100) a movie must have to be recommended')
    )

    include_adult_content = models.BooleanField(
        _('include adult content'),
        default=False
    )

    recommendation_frequency = models.CharField(
        _('recommendation frequency'),
        max_length=20,
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('biweekly', _('Bi-weekly')),
            ('monthly', _('Monthly')),
            ('never', _('Never')),
        ],
        default='weekly'
    )

    # Display preferences
    items_per_page = models.IntegerField(
        _('items per page'),
        default=20,
        choices=[(10, '10'), (20, '20'), (50, '50'), (100, '100')]
    )

    default_sort_order = models.CharField(
        _('default sort order'),
        max_length=20,
        choices=[
            ('rating_desc', _('Rating (High to Low)')),
            ('rating_asc', _('Rating (Low to High)')),
            ('date_desc', _('Date (Newest First)')),
            ('date_asc', _('Date (Oldest First)')),
            ('title_asc', _('Title (A to Z)')),
            ('title_desc', _('Title (Z to A)')),
        ],
        default='rating_desc'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('user preferences')
        verbose_name_plural = _('user preferences')

    def __str__(self):
        return f"{self.user.username}'s preferences"


class UserFollowing(models.Model):
    """User following relationship for social features."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followed_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_following'
        unique_together = ('user', 'followed_user')
        verbose_name = _('user following')
        verbose_name_plural = _('user followings')
        indexes = [
            models.Index(fields=['user', 'followed_user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} follows {self.followed_user.username}"
