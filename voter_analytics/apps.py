# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Configure the voter analytics application.
from django.apps import AppConfig


class VoterAnalyticsConfig(AppConfig):
    """Register this application's name and primary key type."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'voter_analytics'
