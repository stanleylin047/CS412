# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: This file set the data and data type we need.
from django.db import models

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
