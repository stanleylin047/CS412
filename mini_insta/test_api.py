from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.test import APITestCase

from .models import Follow, Photo, Post, Profile


class MiniInstaAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.user = users.objects.create_user('alice-login', password='test-password')
        users.objects.create_user('unlinked', password='test-password')
        cls.alice = Profile.objects.create(
            user=cls.user, username='alice', display_name='Alice',
            profile_image_url='https://example.com/alice.png',
        )
        cls.bob = Profile.objects.create(
            username='bob', display_name='Bob', profile_image_url='https://example.com/bob.png',
        )
        Follow.objects.create(profile=cls.bob, follower_profile=cls.alice)
        cls.older_post = Post.objects.create(profile=cls.bob, caption='Older')
        cls.newer_post = Post.objects.create(profile=cls.bob, caption='Newer')
        Photo.objects.create(post=cls.newer_post, image_url='https://example.com/post.png')
        cls.own_post = Post.objects.create(profile=cls.alice, caption='My post')

    def login(self, username='alice-login', password='test-password'):
        return self.client.post(reverse('mini_insta:api_login'), {
            'username': username, 'password': password,
        }, format='json')

    def authenticate(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['profile']['id'], self.alice.pk)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + response.data['token'])

    def test_login_and_authentication(self):
        self.assertEqual(self.login(password='wrong').status_code, 400)
        self.assertEqual(self.login(username='unlinked').status_code, 403)
        self.assertEqual(self.client.get(reverse('mini_insta:api_profiles')).status_code, 401)
        self.assertEqual(self.client.post(reverse('mini_insta:api_create_post'), {
            'caption': 'Anonymous post',
        }).status_code, 401)

    def test_profiles_posts_and_feed(self):
        self.authenticate()
        profiles = self.client.get(reverse('mini_insta:api_profiles'))
        self.assertEqual([profile['id'] for profile in profiles.data], [self.alice.pk, self.bob.pk])
        detail = self.client.get(reverse('mini_insta:api_profile', args=[self.alice.pk]))
        self.assertEqual(detail.data['username'], 'alice')
        self.assertEqual(self.client.get(reverse('mini_insta:api_profile', args=[99999])).status_code, 404)
        posts = self.client.get(reverse('mini_insta:api_profile_posts', args=[self.alice.pk]))
        self.assertEqual([post['id'] for post in posts.data], [self.own_post.pk])

        feed = self.client.get(reverse('mini_insta:api_feed', args=[self.alice.pk]))
        self.assertEqual([post['id'] for post in feed.data], [self.newer_post.pk, self.older_post.pk])
        self.assertEqual(feed.data[0]['photos'][0]['image_url'], 'https://example.com/post.png')
        self.assertEqual(self.client.get(reverse('mini_insta:api_feed', args=[self.bob.pk])).status_code, 403)

    def test_create_post_uses_authenticated_profile(self):
        self.authenticate()
        url = reverse('mini_insta:api_create_post')
        self.assertEqual(self.client.post(url, {'caption': '  '}, format='json').status_code, 400)
        response = self.client.post(url, {
            'caption': 'New caption',
            'image_url': 'https://example.com/new.png',
            'profile': self.bob.pk,
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get(pk=response.data['id']).profile, self.alice)
        self.assertEqual(response.data['photos'][0]['image_url'], 'https://example.com/new.png')

    @override_settings(STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    })
    def test_create_post_with_uploaded_photo(self):
        self.authenticate()
        image = BytesIO()
        Image.new('RGB', (4, 4)).save(image, format='PNG')
        upload = SimpleUploadedFile('photo.png', image.getvalue(), content_type='image/png')
        response = self.client.post(reverse('mini_insta:api_create_post'), {
            'image_file': upload,
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        photo = Photo.objects.get(post_id=response.data['id'])
        self.assertTrue(photo.image_file.storage.exists(photo.image_file.name))
        self.assertEqual(response.data['photos'][0]['image_url'],
                         'http://testserver' + photo.image_file.url)
