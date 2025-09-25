"""
URL configuration for API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()

urlpatterns = [
    path('v1/', include(router.urls)),
]