# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Route voter listings, individual records, and aggregate graphs.
from django.urls import path
from .views import VotersListView, VoterDetailView, GraphsView

app_name = 'voter_analytics'
urlpatterns = [
    path('', VotersListView.as_view(), name='voters'),
    path('voter/<int:pk>', VoterDetailView.as_view(), name='voter'),
    path('graphs', GraphsView.as_view(), name='graphs'),
]
