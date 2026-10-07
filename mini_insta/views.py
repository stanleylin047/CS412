# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Display the profile list and individual profile pages.
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from .models import Profile, Post, Photo
from .forms import CreatePostForm

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

class CreatePostView(CreateView):
    """Create a post and one photo for the profile identified by the URL."""

    model = Post
    form_class = CreatePostForm
    template_name = 'mini_insta/create_post_form.html'

    def get_context_data(self, **kwargs):
        """
        Add the profile to the template context.

        self is the current view instance.
        kwargs contains context values supplied by the parent view.
        """
        context = super().get_context_data(**kwargs)
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        context['profile'] = profile
        return context

    def form_valid(self, form):
        """
        Attach the profile, save the post, and create its photo.

        self is the current view instance.
        form is the validated CreatePostForm submitted by the user.
        """
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        form.instance.profile = profile

        response = super().form_valid(form)

        image_url = self.request.POST['image_url']
        Photo.objects.create(
            post=self.object,
            image_url=image_url,
        )

        return response