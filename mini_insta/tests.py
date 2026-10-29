# Name: Stanley Lin
# BU Email: stanley0@bu.edu
# Description: Verify profile editing, posts, social data, feeds, and search.
from django.test import TestCase
from django.urls import reverse
from .models import Profile, Post, Photo, Follow, Comment, Like


class MiniInstaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = Profile.objects.create(username='reader', display_name='Reader', profile_image_url='https://example.com/reader.jpg')
        cls.author = Profile.objects.create(username='artist', display_name='Painter', bio_text='Mountain explorer', profile_image_url='https://example.com/artist.jpg')
        cls.other = Profile.objects.create(username='other', display_name='Other', profile_image_url='https://example.com/other.jpg')
        Follow.objects.create(profile=cls.author, follower_profile=cls.viewer)
        cls.post = Post.objects.create(profile=cls.author, caption='Mountain sunrise')
        cls.newer = Post.objects.create(profile=cls.author, caption='Newest painting')
        cls.unfollowed = Post.objects.create(profile=cls.other, caption='Unfollowed post')
        Photo.objects.create(post=cls.post, image_url='https://example.com/mountain.jpg')
        Comment.objects.create(post=cls.post, profile=cls.viewer, text='Beautiful view!')
        Like.objects.create(post=cls.post, profile=cls.viewer)

    def url(self, name, pk=None):
        return reverse('mini_insta:' + name, kwargs={'pk': pk or self.viewer.pk})

    def test_profile_update_preserves_account_fields(self):
        url = self.url('update_profile')
        response = self.client.get(url)
        self.assertEqual(response.context['form'].initial['display_name'], 'Reader')
        self.assertNotIn('username', response.context['form'].fields)
        self.assertNotIn('join_date', response.context['form'].fields)
        joined = self.viewer.join_date
        response = self.client.post(url, {'display_name': 'Updated', 'profile_image_url': 'https://example.com/new.jpg', 'bio_text': 'New bio', 'username': 'changed'})
        self.assertRedirects(response, self.viewer.get_absolute_url())
        self.viewer.refresh_from_db()
        self.assertEqual((self.viewer.display_name, self.viewer.username, self.viewer.join_date), ('Updated', 'reader', joined))

    def test_post_update_and_delete(self):
        response = self.client.post(self.url('update_post', self.post.pk), {'caption': 'Edited caption', 'profile': self.other.pk})
        self.assertRedirects(response, self.post.get_absolute_url())
        self.post.refresh_from_db()
        self.assertEqual(self.post.caption, 'Edited caption')
        self.assertEqual(self.post.profile, self.author)
        url = self.url('delete_post', self.post.pk)
        response = self.client.get(url)
        self.assertEqual(response.context['profile'], self.author)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())
        response = self.client.post(url)
        self.assertRedirects(response, self.author.get_absolute_url())
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
        self.assertFalse(Photo.objects.filter(post_id=self.post.pk).exists())
        self.assertFalse(Comment.objects.filter(post_id=self.post.pk).exists())
        self.assertFalse(Like.objects.filter(post_id=self.post.pk).exists())

    def test_social_accessors_and_feed(self):
        self.assertEqual(self.author.get_followers(), [self.viewer])
        self.assertEqual(self.viewer.get_following(), [self.author])
        self.assertEqual(self.author.get_num_followers(), 1)
        self.assertEqual(self.viewer.get_num_following(), 1)
        self.assertEqual(self.other.get_followers(), [])
        self.assertEqual(list(self.viewer.get_post_feed()), [self.newer, self.post])
        self.assertEqual(list(self.other.get_post_feed()), [])
        response = self.client.get(self.url('show_feed'))
        self.assertContains(response, 'Beautiful view!')
        self.assertContains(response, '1 likes')
        self.assertContains(response, 'https://example.com/mountain.jpg')
        self.assertNotContains(response, 'Unfollowed post')

    def test_pages_and_navigation(self):
        self.assertEqual(self.client.get(reverse('mini_insta:show_all_profiles')).status_code, 200)
        for name in ['show_profile', 'show_followers', 'show_following', 'show_feed', 'update_profile', 'create_post']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(self.url(name)).status_code, 200)
        response = self.client.get(self.post.get_absolute_url())
        self.assertContains(response, 'Beautiful view!')
        self.assertContains(response, '1 likes')
        self.assertContains(response, self.url('search', self.author.pk))

    def test_search_form_and_matching_fields(self):
        url = self.url('search')
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'mini_insta/search.html')
        self.assertEqual(response.context['profile'], self.viewer)
        for query in ['ARTIST', 'painter', 'explorer']:
            with self.subTest(query=query):
                response = self.client.get(url, {'query': query})
                self.assertTemplateUsed(response, 'mini_insta/search_results.html')
                self.assertEqual(list(response.context['profiles']), [self.author])
        response = self.client.get(url, {'query': '  MOUNTAIN  '})
        self.assertEqual(list(response.context['posts']), [self.post])
        self.assertEqual(list(response.context['profiles']), [self.author])
        self.assertEqual(response.context['profile'], self.viewer)
        self.assertContains(response, self.post.get_absolute_url())

    def test_search_empty_missing_and_escaped_queries(self):
        url = self.url('search')
        for query in ['', '   ', 'no matching data', '<script>alert(1)</script>']:
            with self.subTest(query=query):
                response = self.client.get(url, {'query': query})
                self.assertEqual(list(response.context['posts']), [])
                self.assertEqual(list(response.context['profiles']), [])
                self.assertNotContains(response, '<script>')
        self.assertEqual(self.client.get(self.url('search', 99999)).status_code, 404)
        self.assertEqual(self.client.get(self.url('search', 99999), {'query': 'artist'}).status_code, 404)
