"""
URL configuration for CamFlix project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from apps.movies.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('api/', include('apps.api.urls')),
]

# Internationalized URLs
urlpatterns += i18n_patterns(
    path('', home_view, name='home'),
    path('accounts/', include('apps.accounts.urls')),
    path('movies/', include('apps.movies.urls')),
    path('ratings/', include('apps.ratings.urls')),
    path('recommendations/', include('apps.recommendations.urls')),
)

# Debug toolbar
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# Static and media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
