# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Display the profile list and individual profile pages.
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Profile, Post, Photo
from .forms import CreatePostForm, UpdatePostForm, UpdateProfileForm
from django.urls import reverse
from django.db.models import Q

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

        #Created one photo with an external image URL.
        #image_url = self.request.POST['image_url']
        #Photo.objects.create(
        #    post=self.object,
        #    image_url=image_url,
        #)

        files = self.request.FILES.getlist('files')

        for image_file in files:
            Photo.objects.create(
                post=self.object,
                image_file=image_file,
            )

        return response

class UpdateProfileView(UpdateView):
    """Display and process edits to an existing profile."""
    model = Profile
    form_class = UpdateProfileForm
    template_name = 'mini_insta/update_profile_form.html'
    context_object_name = 'profile'

class UpdatePostView(UpdateView):
    '''Display and process edits to an existing post caption.'''
    model = Post
    form_class = UpdatePostForm
    template_name = 'mini_insta/update_post_form.html'
    context_object_name = 'post'

class DeletePostView(DeleteView):
    '''Delete an existing post.'''

    model = Post
    template_name = 'mini_insta/delete_post_form.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        """
        Add the post author's profile to the template context.

        self is the current view instance.
        kwargs contains context values supplied by the parent view.
        """

        context = super().get_context_data(**kwargs)
        context['profile'] = self.object.profile
        return context

    def get_success_url(self):
        """
        Return the author's profile URL after deletion.

        self is the current view instance.
        """
        return reverse('mini_insta:show_profile', kwargs={'pk': self.object.profile_id})

class ShowFollowersDetailView(DetailView):
    """Display the followers of a selected profile."""

    model = Profile
    template_name = 'mini_insta/show_followers.html'
    context_object_name = 'profile'


class ShowFollowingDetailView(DetailView):
    """Display the profiles followed by a selected profile."""

    model = Profile
    template_name = 'mini_insta/show_following.html'
    context_object_name = 'profile'

class ShowFeedView(DetailView):
    """Display posts from profiles followed by the selected profile."""

    model = Profile
    template_name = 'mini_insta/show_feed.html'
    context_object_name = 'profile'


class SearchView(ListView):
    """Search post captions and profiles on behalf of a selected profile."""

    template_name = 'mini_insta/search_results.html'
    context_object_name = 'posts'

    def dispatch(self, request, *args, **kwargs):
        """Show the search form until a query is submitted."""
        self.profile = get_object_or_404(Profile, pk=kwargs['pk'])
        if 'query' not in request.GET:
            return render(request, 'mini_insta/search.html', {'profile': self.profile})
        self.query = request.GET.get('query', '').strip()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """Return matching captions, with the most recent posts first."""
        if not self.query:
            return Post.objects.none()
        return Post.objects.filter(caption__icontains=self.query).order_by('-timestamp', '-pk')

    def get_context_data(self, **kwargs):
        """Include the searching profile, query, and matching profiles."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        context['query'] = self.query
        context['profiles'] = Profile.objects.filter(
            Q(username__icontains=self.query)
            | Q(display_name__icontains=self.query)
            | Q(bio_text__icontains=self.query)
        ).order_by('username', 'pk') if self.query else Profile.objects.none()
        return context
