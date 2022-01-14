from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        """создание юзера"""
        cls.user = User.objects.create_user(username='TestName')

        """создание тестовой группы"""
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='TestGroup',
            description='TestGroup for test',
        )

        """создание поста"""
        cls.post = Post.objects.create(
            # id=2,
            text='TestPost',
            author=cls.user,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        user = PostCreateFormTests.user
        self.authorized_client.force_login(user)

    def test_create_post(self):
        """создание нового поста"""
        post_count = Post.objects.count()

        form_data = {
            # 'id': 1,
            'text': 'Test text',
            'group': self.group.id,
        }

        cache.clear()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )

        self.assertEqual(Post.objects.count(), post_count + 1)

        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())
        self.assertTrue(Post.objects.filter(group=self.group).exists())
        self.assertTrue(Post.objects.filter(author=self.user).exists())

    def test_edit_post(self):
        """редактирование существующего поста"""
        form_data = {
            'text': 'New Test text',
        }

        cache.clear()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )

        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

    def test_create_post_not_login_user(self):
        """попытка создание нового поста с неавторизованным юзером"""
        post_count = Post.objects.count()

        form_data = {
            'text': 'Test text',
            'group': self.group.id,
        }

        cache.clear()
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        expected_url = (reverse('users:login')
                        + "?next="
                        + reverse('posts:post_create'))
        self.assertRedirects(response, expected_url)

        self.assertEqual(Post.objects.count(), post_count)

    def test_add_comment(self):
        """добавление комментария к посту"""
        comment_count = self.post.comments.count()

        form_data = {
            'text': 'Test comment',
            'post': self.post,
        }

        cache.clear()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

        self.assertEqual(self.post.comments.count(), comment_count + 1)

    def test_add_comment_not_login_user(self):
        """попытка добавления комментарий с неавторизованным юзером"""
        comment_count = self.post.comments.count()

        form_data = {
            'text': 'Test comment',
            'post': self.post,
        }

        cache.clear()
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        expected_url = (reverse('users:login')
                        + "?next="
                        + reverse('posts:add_comment',
                                  kwargs={'post_id': self.post.id}))

        self.assertRedirects(response, expected_url)

        self.assertEqual(self.post.comments.count(), comment_count)
