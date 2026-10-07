# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Define the form used to create a Mini Insta post.

from django import forms
from .models import Post


class CreatePostForm(forms.ModelForm):
    """Collect the caption for a new post."""

    class Meta:
        """Specify the model and fields used by this form."""

        model = Post
        fields = ['caption']