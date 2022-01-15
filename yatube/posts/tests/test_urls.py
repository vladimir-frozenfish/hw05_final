from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from http import HTTPStatus


from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            title='TestGroup',
            slug='TestGroup',
            description='TestGroup for test',
        )

        """создание юзеров"""
        cls.user = User.objects.create_user(username='TestName')
        cls.user_2 = User.objects.create_user(username='TestName_2')

        """создание поста с авторстом первого юзера"""
        cls.post = Post.objects.create(
            text='TestPost post for testing',
            author=cls.user,
            group=cls.group
        )

        """создание поста с авторстом второго юзера"""
        cls.post2 = Post.objects.create(
            text='TestPost post for testing_2',
            author=cls.user_2,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        user = PostsURLTests.user
        self.authorized_client.force_login(user)

    def test_page_not_login_user(self):
        """проверка доступности страниц для неавторизованного пользователя
        c использование словаря"""
        page_status = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }

        for url, status_page in page_status.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status_page)

    def test_page_not_login_user_redirect(self):
        """ проверка редиректов для неавторизованного пользователя
        c использованием словаря"""
        page_redirect = {
            '/create/': '/auth/login/?next=%2Fcreate%2F',
            f'/posts/{self.post.id}/edit/': f'/posts/{self.post.id}/',
            f'/posts/{self.post.id}/comment/':
                f'/auth/login/?next=/posts/{self.post.id}/comment/',
            '/follow/': '/auth/login/?next=/follow/',
            f'/profile/{self.user}/follow/':
                f'/auth/login/?next=/profile/{self.user}/follow/',
            f'/profile/{self.user}/unfollow/':
                f'/auth/login/?next=/profile/{self.user}/unfollow/',
        }

        for url, redirect in page_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_page_login_user(self):
        """проверка доступности страниц для авторизованного пользователя
        c использование словаря"""
        page_status = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.OK,
            f'/posts/{self.post.id}/comment/': HTTPStatus.FOUND,
            '/follow/': HTTPStatus.OK,
            f'/profile/{self.user_2}/follow/': HTTPStatus.FOUND,
            f'/profile/{self.user_2}/unfollow/': HTTPStatus.FOUND
        }

        for url, status_page in page_status.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, status_page)

    def test_post_edit_redirect_not_author(self):
        """Проверка страницы редактирования поста для авторизованного
        пользователя, но не создателя данного поста"""
        response = self.authorized_client.get(f'/posts/{self.post2.id}/edit/')
        self.assertRedirects(response, f'/posts/{self.post2.id}/')

    def test_urls_uses_correct_template(self):
        """Проверка вызываемых шаблонов для каждого адреса
        URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
