# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Register Profile for management in the Django admin.
from django.contrib import admin

# Register your models here.
from .models import Profile, Post, Photo

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Photo)

