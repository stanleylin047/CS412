from django.urls import path
from . import views, api_views

app_name = "dadjokes"
urlpatterns = [
    path("", views.random_page, name="home"),
    path("random", views.random_page, name="random"),
    path("jokes", views.jokes_page, name="jokes"),
    path("joke/<int:pk>", views.joke_page, name="joke"),
    path("pictures", views.pictures_page, name="pictures"),
    path("picture/<int:pk>", views.picture_page, name="picture"),

    path("api/", api_views.random_joke_api),
    path("api/random", api_views.random_joke_api),
    path("api/jokes", api_views.jokes_api),
    path("api/joke/<int:pk>", api_views.joke_api),
    path("api/pictures", api_views.pictures_api),
    path("api/picture/<int:pk>", api_views.picture_api),
    path("api/random_picture", api_views.random_picture_api),
]