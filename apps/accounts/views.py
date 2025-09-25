"""
Views for accounts app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _


@login_required
def profile_view(request):
    """User profile view."""
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def settings_view(request):
    """User settings view."""
    if request.method == 'POST':
        # Handle settings update
        user = request.user

        # Update basic profile fields
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.bio = request.POST.get('bio', user.bio)

        # Update preferences
        user.preferred_language = request.POST.get('preferred_language', user.preferred_language)

        # Update notification preferences
        user.email_notifications = request.POST.get('email_notifications') == 'on'

        # Save the user
        user.save()

        # Handle user preferences (create if doesn't exist)
        from .models import UserPreferences
        preferences, created = UserPreferences.objects.get_or_create(user=user)
        preferences.include_adult_content = request.POST.get('show_adult_content') == 'on'
        preferences.save()

        messages.success(request, _('Settings updated successfully'))
        return redirect('accounts:settings')

    # Get or create user preferences
    from .models import UserPreferences
    try:
        preferences = request.user.preferences
    except UserPreferences.DoesNotExist:
        preferences = None

    context = {
        'user': request.user,
        'preferences': preferences,
    }
    return render(request, 'accounts/settings.html', context)
