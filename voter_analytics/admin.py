# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Make voter records available in the Django admin.
from django.contrib import admin
from .models import Voter


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    """Provide searchable voter names and basic filters in the admin."""

    list_display = ['last_name', 'first_name', 'party_affiliation', 'voter_score']
    search_fields = ['last_name', 'first_name', 'voter_id']
    list_filter = ['party_affiliation', 'voter_score']
