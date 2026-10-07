# Name: Stanley Lin
# Email: stanley0@bu.edu
# File: urls.py
# Description: This file defines the URL patterns for the mini_insta application.
from django.urls import path
from .views import ProfileListView, ProfileDetailView, PostDetailView, CreatePostView

app_name = "mini_insta"

urlpatterns = [
    path('', ProfileListView.as_view(), name="show_all_profiles"),
    path('profile/<int:pk>', ProfileDetailView.as_view(), name="show_profile"),
    path('post/<int:pk>', PostDetailView.as_view(), name="show_post"),
    path('profile/<int:pk>/create_post', CreatePostView.as_view(), name="create_post"),
]
