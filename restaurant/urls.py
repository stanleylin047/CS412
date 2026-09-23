# Name: Stanley
# Email: stanley0@bu.edu
# File: urls.py
# Description: This file defines the URL patterns for the restaurant application.

from django.urls import path
from . import views

app_name = "restaurant"

urlpatterns = [
    path("main", views.main, name="main"),
    path("order", views.order, name="order"),
    path("confirmation", views.confirmation, name="confirmation"),
]
