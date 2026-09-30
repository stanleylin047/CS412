# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Register Profile for management in the Django admin.
from django.contrib import admin

# Register your models here.
from .models import Profile
admin.site.register(Profile)
