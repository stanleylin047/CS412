# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Define the form used to create a Mini Insta post.

from django import forms
from .models import Post, Profile


class CreatePostForm(forms.ModelForm):
    """Collect the caption for a new post."""

    class Meta:
        """Specify the model and fields used by this form."""

        model = Post
        fields = ['caption']

class UpdateProfileForm(forms.ModelForm):
    """Collect editable information for an existing profile."""

    class Meta:
        """Choose the model and fields used by this form."""
        model = Profile
        fields = ['display_name', 'profile_image_url', 'bio_text']

class UpdatePostForm(forms.ModelForm):

    class Meta:

        model = Post
        fields = ['caption']

