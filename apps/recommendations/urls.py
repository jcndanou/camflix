"""
URL configuration for recommendations app.
"""

from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('for-you/', views.for_you_view, name='for-you'),
]