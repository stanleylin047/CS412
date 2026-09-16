from django.shortcuts import render
import random

# Create your views here.
quotes = [
    "Those times when you get up early and you work hard; those times when you stay up late and you work hard; those times when you don’t feel like working, you’re too tired, you don’t want to push yourself, but you do it anyway; that is actually the dream. That’s the dream. It’s not the destination, it’s the journey.",
    "someone has to win, so why not me.",
    "I never needed any external forces to motivate me.",

]

images = [
    "https://media.gettyimages.com/id/102186206/photo/los-angeles-ca-kobe-bryant-of-the-los-angeles-lakers-celebrates-after-the-lakers-defeated-the.jpg?s=612x612&w=0&k=20&c=LjturNxqRpgYhvgsvyo2URpdOSFIuUaGD9XGLZlrbuM=",
    "https://media.gettyimages.com/id/914624594/photo/beverly-hills-ca-kobe-bryant-attends-the-90th-annual-academy-awards-nominee-luncheon-at-the.jpg?s=612x612&w=0&k=20&c=5OZOzobE6UhIzvn0hX4kaZWn1gCEuJNbbn4xjLGQtYA=",
    "https://media.gettyimages.com/id/73617497/photo/los-angeles-ca-kobe-bryant-of-the-los-angeles-lakers-plays-defense-against-the-portland-trail.jpg?s=612x612&w=0&k=20&c=FUcvYtb45z7r27jYuCYydThp90-LGs0VtI4PYH9_0sE=",
]

def quote(request):
    selected_quote = random.choice(quotes)
    selected_image = random.choice(images)

    context = {
        "quote": selected_quote,
        "image": selected_image,
    }

    return render(request, "quote.html", context)

def show_all(request):
    context = {
        "quotes": quotes,
        "images": images,
    }
    return render(request, "show_all.html", context)

def about(request):
    return render(request, "about.html")