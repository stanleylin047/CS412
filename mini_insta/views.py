# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Display the profile list and individual profile pages.
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Profile, Post

# Create your views here.
class ProfileListView(ListView):
    """Display all profiles using the profile list template."""
    
    model = Profile
    template_name = "mini_insta/show_all_profiles.html"
    context_object_name = "profiles"

class ProfileDetailView(DetailView):
    """Display the profile selected by its primary key."""

    model = Profile
    template_name = "mini_insta/show_profile.html"
    context_object_name = "profile"

class PostDetailView(DetailView):
    """Display one post selected by its primary key."""

    model = Post
    template_name = "mini_insta/show_post.html"
    context_object_name = "post"
