from django.shortcuts import render, get_object_or_404
from .models import Joke, Picture

# Create your views here.

def random_page(request):
    return render(request, "dadjokes/random.html", {
        "joke": Joke.objects.order_by("?").first(),
        "picture": Picture.objects.order_by("?").first(),
        })

def jokes_page(request):
    jokes = Joke.objects.all()

    return render(request, "dadjokes/jokes.html", {"jokes": jokes})

def pictures_page(request):
    pictures = Picture.objects.all()

    return render(request, "dadjokes/pictures.html", {"pictures": pictures})

def joke_page(request, pk):
    joke = get_object_or_404(Joke, pk=pk)

    return render(request, "dadjokes/joke.html", {
        "joke": joke
    })

def picture_page(request, pk):
    picture = get_object_or_404(Picture, pk=pk)

    return render(request, "dadjokes/picture.html", {
        "picture": picture
    })
