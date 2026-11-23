from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Photo, Post, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'username', 'display_name', 'profile_image_url', 'bio_text', 'join_date')


class PhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ('id', 'image_url')

    def get_image_url(self, photo):
        url = photo.get_image_url()
        if url:
            return self.context['request'].build_absolute_uri(url)
        return ''


class PostSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    photos = PhotoSerializer(source='photo_set', many=True, read_only=True)
    image_url = serializers.URLField(write_only=True, required=False)
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Post
        fields = ('id', 'profile', 'timestamp', 'caption', 'photos', 'image_url', 'image_file')

    def validate(self, attrs):
        image_url = attrs.get('image_url')
        image_file = attrs.get('image_file')
        if image_url and image_file:
            raise serializers.ValidationError('Choose either an image URL or an image file.')
        if not (attrs.get('caption') or image_url or image_file):
            raise serializers.ValidationError('Add a caption or an image.')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        image_url = validated_data.pop('image_url', '')
        image_file = validated_data.pop('image_file', None)
        post = super().create(validated_data)
        if image_url or image_file:
            Photo.objects.create(post=post, image_url=image_url, image_file=image_file)
        return post


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        credentials = AuthTokenSerializer(data=request.data, context={'request': request})
        credentials.is_valid(raise_exception=True)
        user = credentials.validated_data['user']
        profile = get_account_profile(user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'profile': ProfileSerializer(profile).data})


def get_account_profile(user):
    profile = getattr(user, 'mini_insta_profile', None)
    if profile is None:
        raise PermissionDenied('This account is not linked to a MiniInsta profile.')
    return profile


class AuthenticatedAPI:
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


class ProfileList(AuthenticatedAPI, generics.ListAPIView):
    queryset = Profile.objects.order_by('username', 'pk')
    serializer_class = ProfileSerializer


class ProfileDetail(AuthenticatedAPI, generics.RetrieveAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class ProfilePosts(AuthenticatedAPI, generics.ListAPIView):
    serializer_class = PostSerializer

    def get_posts(self, profile):
        return profile.get_all_posts().order_by('-timestamp', '-pk')

    def get_queryset(self):
        profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return self.get_posts(profile).select_related('profile').prefetch_related(
            Prefetch('photo_set', queryset=Photo.objects.order_by('timestamp', 'pk')),
        )


class ProfileFeed(ProfilePosts):
    def get_posts(self, profile):
        if profile.pk != get_account_profile(self.request.user).pk:
            raise PermissionDenied('You can only read your own feed.')
        return profile.get_post_feed()


class CreatePost(AuthenticatedAPI, generics.CreateAPIView):
    serializer_class = PostSerializer

    def perform_create(self, serializer):
        serializer.save(profile=get_account_profile(self.request.user))
