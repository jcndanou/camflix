"""
Admin configuration for ratings app.
"""

from django.contrib import admin
from .models import Rating, Review, ReviewReaction, ReviewComment


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'tier', 'created_at']
    list_filter = ['tier', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'movie__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Informations', {
            'fields': ('user', 'movie')
        }),
        ('Notation', {
            'fields': ('score', 'tier')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        })
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'title', 'created_at', 'reaction_count']
    list_filter = ['created_at', 'moderation_status']
    search_fields = ['user__username', 'movie__title', 'title', 'content']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Informations', {
            'fields': ('id', 'user', 'movie', 'rating')
        }),
        ('Contenu', {
            'fields': ('title', 'content')
        }),
        ('Modération', {
            'fields': ('moderation_status',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        })
    )

    def reaction_count(self, obj):
        return obj.reactions.count()
    reaction_count.short_description = 'Réactions'


@admin.register(ReviewReaction)
class ReviewReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'review', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['user__username', 'review__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
