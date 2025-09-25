"""
Signal handlers for accounts app.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserPreferences


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """Create UserPreferences when a new User is created."""
    if created:
        UserPreferences.objects.create(user=instance)


@receiver(post_save, sender=User)
def create_recommendation_profile(sender, instance, created, **kwargs):
    """Create RecommendationProfile when a new User is created."""
    if created:
        from apps.recommendations.models import RecommendationProfile
        RecommendationProfile.objects.create(user=instance)