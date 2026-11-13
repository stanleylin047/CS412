from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Joke, Picture
from .serializers import JokeSerializer, PictureSerializer


# GET one random joke
@api_view(["GET"])
def random_joke_api(request):
    joke = Joke.objects.order_by("?").first()

    if joke is None:
        return Response(
            {"detail": "No jokes available."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(JokeSerializer(joke).data)


# GET all jokes or POST a new joke
@api_view(["GET", "POST"])
def jokes_api(request):
    if request.method == "GET":
        jokes = Joke.objects.all().order_by("id")
        return Response(JokeSerializer(jokes, many=True).data)

    serializer = JokeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED,
    )


# GET one joke by its primary key
@api_view(["GET"])
def joke_api(request, pk):
    joke = get_object_or_404(Joke, pk=pk)
    return Response(JokeSerializer(joke).data)


# GET all pictures
@api_view(["GET"])
def pictures_api(request):
    pictures = Picture.objects.all().order_by("id")
    return Response(PictureSerializer(pictures, many=True).data)


# GET one picture by its primary key
@api_view(["GET"])
def picture_api(request, pk):
    picture = get_object_or_404(Picture, pk=pk)
    return Response(PictureSerializer(picture).data)


# GET one random picture
@api_view(["GET"])
def random_picture_api(request):
    picture = Picture.objects.order_by("?").first()

    if picture is None:
        return Response(
            {"detail": "No pictures available."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(PictureSerializer(picture).data)