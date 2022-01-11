from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_author(self):
        """Проверяем, что страница "Об авторе" работает."""
        response = self.guest_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_tech(self):
        """Проверяем, что страница "Технологии" работает."""
        response = self.guest_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)
