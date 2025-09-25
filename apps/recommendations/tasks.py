"""
Celery tasks for recommendations app.
"""

from celery import shared_task
from django.db.models import Count, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
import numpy as np
from scipy.stats import pearsonr

from apps.accounts.models import User
from apps.movies.models import Movie
from apps.ratings.models import Rating
from .models import UserSimilarity, Recommendation

logger = logging.getLogger(__name__)


@shared_task
def calculate_all_user_similarities():
    """Calculate similarity scores between all users."""
    try:
        users = User.objects.filter(
            ratings__isnull=False
        ).distinct()

        total_calculations = 0

        for i, user1 in enumerate(users):
            for user2 in users[i+1:]:
                similarity = calculate_user_similarity(user1.id, user2.id)
                if similarity is not None:
                    total_calculations += 1

        logger.info(f"Calculated {total_calculations} user similarities")
        return f"Calculated {total_calculations} similarities"

    except Exception as e:
        logger.error(f"Failed to calculate user similarities: {e}")
        raise


@shared_task
def calculate_user_similarity(user1_id: int, user2_id: int):
    """Calculate similarity between two users based on their ratings."""
    try:
        user1 = User.objects.get(id=user1_id)
        user2 = User.objects.get(id=user2_id)

        # Get common rated movies
        user1_ratings = Rating.objects.filter(user=user1).values_list('movie_id', 'score')
        user2_ratings = Rating.objects.filter(user=user2).values_list('movie_id', 'score')

        user1_dict = dict(user1_ratings)
        user2_dict = dict(user2_ratings)

        common_movies = set(user1_dict.keys()) & set(user2_dict.keys())

        if len(common_movies) < 3:
            # Not enough common movies for meaningful similarity
            return None

        # Prepare arrays for correlation
        scores1 = [user1_dict[movie_id] for movie_id in common_movies]
        scores2 = [user2_dict[movie_id] for movie_id in common_movies]

        # Calculate Pearson correlation
        if len(set(scores1)) > 1 and len(set(scores2)) > 1:
            correlation, _ = pearsonr(scores1, scores2)

            # Normalize to 0-1 range
            similarity_score = (correlation + 1) / 2
        else:
            # If one user has constant ratings, use simple difference
            similarity_score = 1 - (np.mean(np.abs(np.array(scores1) - np.array(scores2))) / 100)

        # Update or create similarity record
        UserSimilarity.objects.update_or_create(
            user1=user1 if user1.id < user2.id else user2,
            user2=user2 if user1.id < user2.id else user1,
            defaults={
                'similarity_score': max(0, min(1, similarity_score)),
                'common_movies_count': len(common_movies),
                'calculation_method': 'pearson'
            }
        )

        return similarity_score

    except Exception as e:
        logger.error(f"Failed to calculate similarity for users {user1_id} and {user2_id}: {e}")
        return None


@shared_task
def generate_user_recommendations(user_id: int):
    """Generate movie recommendations for a specific user."""
    try:
        user = User.objects.get(id=user_id)

        # Get similar users
        similar_users = UserSimilarity.objects.filter(
            user1=user
        ).union(
            UserSimilarity.objects.filter(user2=user)
        ).order_by('-similarity_score')[:20]

        # Get movies rated highly by similar users
        similar_user_ids = []
        for similarity in similar_users:
            other_user = similarity.user2 if similarity.user1 == user else similarity.user1
            similar_user_ids.append(other_user.id)

        # Get movies not seen by the user but liked by similar users
        user_movie_ids = Rating.objects.filter(user=user).values_list('movie_id', flat=True)

        recommended_movies = Movie.objects.filter(
            ratings__user_id__in=similar_user_ids,
            ratings__score__gte=70
        ).exclude(
            id__in=user_movie_ids
        ).annotate(
            avg_score=Avg('ratings__score'),
            rating_count=Count('ratings')
        ).filter(
            rating_count__gte=2
        ).order_by('-avg_score')[:50]

        # Create recommendation records
        recommendations_created = 0
        for movie in recommended_movies:
            recommendation, created = Recommendation.objects.update_or_create(
                user=user,
                movie=movie,
                defaults={
                    'recommendation_type': 'collaborative',
                    'confidence_score': movie.avg_score / 100,
                    'reason': f"Recommandé basé sur les utilisateurs similaires"
                }
            )
            if created:
                recommendations_created += 1

        logger.info(f"Generated {recommendations_created} recommendations for user {user_id}")
        return f"Generated {recommendations_created} recommendations"

    except Exception as e:
        logger.error(f"Failed to generate recommendations for user {user_id}: {e}")
        raise


@shared_task
def cleanup_old_recommendations():
    """Clean up old recommendations to keep the database lean."""
    try:
        # Delete recommendations older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = Recommendation.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]

        logger.info(f"Deleted {deleted_count} old recommendations")
        return f"Deleted {deleted_count} old recommendations"

    except Exception as e:
        logger.error(f"Failed to cleanup old recommendations: {e}")
        raise


@shared_task
def send_weekly_recommendations():
    """Send weekly recommendation emails to users."""
    try:
        # Get users with email notifications enabled
        users = User.objects.filter(
            email_notifications=True,
            email__isnull=False
        )

        emails_sent = 0
        for user in users:
            # Get recent recommendations
            recommendations = Recommendation.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).select_related('movie').order_by('-confidence_score')[:10]

            if recommendations:
                # Prepare email content
                subject = "Vos recommandations de films de la semaine - CamFlix"
                html_content = render_to_string(
                    'emails/weekly_recommendations.html',
                    {'user': user, 'recommendations': recommendations}
                )

                # Send email
                send_mail(
                    subject,
                    '',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    html_message=html_content,
                    fail_silently=True
                )
                emails_sent += 1

        logger.info(f"Sent {emails_sent} recommendation emails")
        return f"Sent {emails_sent} emails"

    except Exception as e:
        logger.error(f"Failed to send recommendation emails: {e}")
        raise