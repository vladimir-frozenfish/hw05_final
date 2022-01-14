from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse


from ..models import Group, Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        """количество постов с первой группой"""
        cls.count_post_group = 14

        """количество постов с авторстом первого юзера"""
        cls.count_post_author = 15

        """создание первой тестовой группы"""
        cls.group = Group.objects.create(
            title='TestGroup',
            slug='TestGroup',
            description='TestGroup for test',
        )

        """создание второй тестовой группы"""
        cls.group2 = Group.objects.create(
            title='TestGroup2',
            slug='TestGroup2',
            description='TestGroup2 for test',
        )

        """создание юзера"""
        cls.user = User.objects.create_user(username='TestName')

        """создание постов с первой группой"""
        posts = ([Post(text='TestPost post for testing',
                       author=cls.user, group=cls.group)]
                 * cls.count_post_group)
        Post.objects.bulk_create(posts)

        """создание поста с тестовой группой 2"""
        cls.post2 = Post.objects.create(
            text='Post for testing TestGroup2',
            author=cls.user,
            group=cls.group2
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        user = PostsPagesTests.user
        self.authorized_client.force_login(user)

    def test_pages_uses_correct_template(self):
        """проверяем используемые шаблоны
        URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post2.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post2.id}):
                'posts/create_post.html',
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post2.id})
        )

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post2.id})
        )

        self.assertEqual(
            response.context['post'].text, self.post2.text
        )
        self.assertEqual(response.context['post'].group, self.group2)
        self.assertEqual(response.context['post'].author, self.user)
        self.assertEqual(
            response.context['count_post_author'], self.count_post_author
        )

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом.
        Проверка паджинатора"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']),
                         settings.PAGINATOR_COUNT)

        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.count_post_author - settings.PAGINATOR_COUNT)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом.
        Проверка паджинатора"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.PAGINATOR_COUNT)
        self.assertEqual(response.context['group'], self.group)

        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.count_post_group - settings.PAGINATOR_COUNT)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом.
        Проверка паджинатора"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(len(response.context['page_obj']),
                         settings.PAGINATOR_COUNT)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(
            response.context['count_post_author'], self.count_post_author
        )

        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']),
                         self.count_post_author - settings.PAGINATOR_COUNT)


class PostsCacheTests(TestCase):
    """тестрирование кэша"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='TestCacheName')

        cls.post = Post.objects.create(
            text='Text for cache',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index(self):
        """тестирование кэша главной страницы"""

        """очистка кэша от предыдущих тестов"""
        cache.clear()

        """запрос на страницу с новой записью"""
        self.guest_client.get(reverse('posts:index'))

        """удаление поста"""
        self.post.delete()

        """получение запроса на главной странице с уже удаленной записью из базы данных"""
        response = self.guest_client.get(reverse('posts:index'))

        """проверка, что кэш работает"""
        self.assertIn(self.post.text, response.content.decode('utf-8'))

        """очистка кэша и проверка, что удаленной записи нет на главной странице"""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        self.assertNotIn(self.post.text, response.content.decode('utf-8'))


class FollowPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        """создание юзеров"""
        cls.user_follower = User.objects.create_user(username='UserFollower')
        cls.user_author = User.objects.create_user(username='UserAuthor')

    def setUp(self):
        # self.guest_client = Client()
        self.authorized_client = Client()
        user_follower = FollowPagesTests.user_follower
        self.authorized_client.force_login(user_follower)

    def test_follow_unfollow(self):
        """тест подписки юзера на автора и отписки от него"""
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={'username': self.user_author}))
        self.assertTrue(self.user_author.following.filter(user=self.user_follower).exists())

        self.authorized_client.get(reverse('posts:profile_unfollow', kwargs={'username': self.user_author}))
        self.assertFalse(self.user_author.following.filter(user=self.user_follower).exists())











