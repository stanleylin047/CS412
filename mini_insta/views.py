from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Profile

# Create your views here.
class ProfileListView(ListView):
    
    model = Profile
    template_name = "mini_insta/show_all_profiles.html"
    context_object_name = "profiles"

    def __str__(self):
        '''return a string representation of this model instance'''
        return f'Username: {self.username} Name: {self.display_name}'

class ProfileDetailView(DetailView):

    model = Profile
    template_name = "mini_insta/show_profile.html"
    context_object_name = "profile"
    
