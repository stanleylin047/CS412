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

    def get_absolute_url(self):
        '''return the detail URL for self'''
        return reverse('mini_insta:show_profile', kwargs = {'pk': self.pk},)

    def get_followers(self):
        """Return profiles following self, the current Profile instance."""
        follows = Follow.objects.filter(profile=self)
        return [follow.follower_profile for follow in follows]

    def get_num_followers(self):
        """Return the follower count for self, the current Profile instance."""
        return Follow.objects.filter(profile=self).count()

    def get_following(self):
        """Return profiles followed by self, the current Profile instance."""
        follows = Follow.objects.filter(follower_profile=self)
        return [follow.profile for follow in follows]

    def get_num_following(self):
        """Return the following count for self, the current Profile instance."""
        return Follow.objects.filter(follower_profile=self).count()

    def get_post_feed(self):
        """Return posts by profiles followed by self, newest first."""
        following = self.get_following()

        return Post.objects.filter(
            profile__in=following,
        ).order_by('-timestamp', '-pk')


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

    def get_all_comments(self):
        '''Return comments on self'''
        return Comment.objects.filter(post=self).order_by('timestamp', 'pk')

    def get_likes(self):
        '''Return likes on self'''
        return Like.objects.filter(post=self)
    

class Photo(models.Model):
    """Represent a photo associated with a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to = 'mini_insta/', blank = True,)
    timestamp = models.DateTimeField(auto_now_add=True)

    def get_image_url(self):
        """
        Return the external or uploaded image URL.

        self is the current Photo instance.
        """
        if self.image_url:
            return self.image_url

        if self.image_file:
            return self.image_file.url

        return ''
    
    def __str__(self):
        """Describe the photo; self is the current Photo instance."""
        if self.image_url:
            return f'Post {self.post_id}: {self.image_url}'

        if self.image_file:
            return f'Post {self.post_id}: [self.image_file]'

        return f'Post {self.post_id}: No image'

class Follow(models.Model):
    """Represent one profile following another profile."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    follower_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='follower_profile',
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Describe self, the current Follow relationship."""
        return (
            f'{self.follower_profile.username} follows '
            f'{self.profile.username}'
        )

class Comment(models.Model):
    """Represent a profile's comment on a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    def __str__(self):
        """Describe self, the current Comment instance."""
        return (
            f'{self.profile.username} on post {self.post_id}: '
            f'{self.text[:50]}'
        )


class Like(models.Model):
    """Represent a profile's approval of a post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Describe self, the current Like instance."""
        return f'{self.profile.username} likes post {self.post_id}'