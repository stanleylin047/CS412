# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: This file set the data and data type we need.
from django.db import models
from django.urls import reverse

# Create your models here.
class Profile(models.Model):
    """Encapsulate the data of a user profile"""

    username = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    profile_image_url = models.URLField()
    bio_text = models.TextField(blank=True)
    join_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """return a string representation of this model instance"""
        return f'{self.username}'

    def get_all_posts(self):
        """Return this profile's posts; self is the current Profile instance."""
        return Post.objects.filter(profile=self).order_by('-timestamp')


class Post(models.Model):
    """Represent a post created by a profile"""

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    caption = models.TextField(blank=True)

    def __str__(self):
        """Describe the post; self is the current Post instance."""
        return f'{self.profile.username}: {self.caption[:50]}'

    def get_all_photos(self):
        """Return this post's photos; self is the current Post instance."""
        return Photo.objects.filter(post=self).order_by('timestamp', 'pk')

    def get_absolute_url(self):
        """Return this post's detail URL; self is the current Post instance."""
        return reverse('mini_insta:show_post', kwargs={'pk': self.pk})

class Photo(models.Model):
    """Represent a photo associated with a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image_url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Describe the photo; self is the current Photo instance."""
        return f'Post {self.post_id}: {self.image_url}'
